import uuid
from collections import defaultdict
from datetime import timedelta
from typing import List, Tuple, Optional, Pattern, Union

from django.utils import timezone

from puppy_interactions.interactions.exceptions import (
    UnrecognizedCommandException, CheaterException
)
from puppy_interactions.interactions.models import Person, Interaction
from puppy_interactions.interactions.regex import (
    create_pattern, logs_pattern, clear_pattern, interaction_pattern, days_pattern,
    aggregate_pattern, filter_pattern, help_pattern
)

DEFAULT_LOG_DAYS = 30

"""
Sample data from [Slack API docs](https://api.slack.com/slash-commands) 2019-01-27:

```
token=gIkuvaNzQIHg97ATvDxqgjtO
&team_id=T0001
&team_domain=example
&enterprise_id=E0001
&enterprise_name=Globular%20Construct%20Inc
&channel_id=C2147483705
&channel_name=test
&user_id=U2147483697
&user_name=Steve
&command=/interactions
&text=<@U2147483698> + <@U2147483699> -
&response_url=https://hooks.slack.com/commands/1234/5678
&trigger_id=13345224609.738474920.8088930838d88f008e0
```
"""


def exclusive_match(pattern: Pattern, pattern_list: List[Pattern], text: str) -> bool:
    """
    return True if there is just one match to `pattern`
    return False for ambiguous matches or no match
    """
    if not pattern.match(text):
        return False
    # If there is a match, bool --> int will be a 1; sum to check add'l matches
    return sum([int(bool(p.match(text))) for p in pattern_list]) == 1


def parse_webhook_text(text: str) -> str:
    """
    parse the webhook text and return the desired action:
    * create
    * logs
    * clear
    * help
    """
    pattern_list = [create_pattern, logs_pattern, clear_pattern, help_pattern]

    text = text.strip()
    if exclusive_match(clear_pattern, pattern_list, text):
        return "clear"
    elif exclusive_match(create_pattern, pattern_list, text):
        return "create"
    elif exclusive_match(logs_pattern, pattern_list, text):
        return "logs"
    elif exclusive_match(help_pattern, pattern_list, text):
        return "help"
    else:
        raise UnrecognizedCommandException(text)


def text_to_interaction_tuples(text: str) -> List[Tuple[str, str]]:
    """convert the webhook text to interaction tuples like ("Somebody Galguy", "+")`

    we should convert escaped `user_id`s to plaintext: `<@U23429987>` to `@U23429987`"""
    interactions = [x[0] for x in interaction_pattern.findall(text)]
    interactions = [(x[:-2].strip().replace("<", "").replace(">", ""), x[-1])
                    for x in interactions]
    return interactions


def create_interactions(rater_user_id: str,
                        *args: Tuple[str, str]) -> List[Interaction]:
    """create Interactions from one or many tuple(s) containing the ratee and rating,
    like: `("Somebody Galguy", "+")` """
    rater, _ = Person.objects.get_or_create(user_id=rater_user_id)
    conversation = uuid.uuid4()
    interactions = []
    for interaction in args:
        ratee, _ = Person.objects.get_or_create(user_id=interaction[0])
        rating = interaction[1]

        if ratee == rater:
            raise CheaterException("You can't rate yourself.")

        if rating not in [Interaction.POSITIVE, Interaction.NEGATIVE]:
            raise TypeError(f"Invalid arg for rating - use '{Interaction.POSITIVE}' or "
                            f"'{Interaction.NEGATIVE}'.")
        interactions.append(Interaction(rater=rater, ratee=ratee, rating=rating,
                                        conversation=conversation))
    return Interaction.objects.bulk_create(interactions)


def parse_log_request_text(text: str) -> Tuple[int, Optional[str], Optional[str]]:
    """turn the webhook request text into a tuple of args to retrieval function
    tuple is like (days, aggregate, filter)"""

    def try_get(matches, ret_int=False) -> Optional[Union[int, str]]:
        """get the first element of a list or None"""
        try:
            m = matches[0]
            if ret_int:
                return int(m)
            else:
                return m
        except IndexError:
            return None

    return (
        try_get(days_pattern.findall(text), ret_int=True) or DEFAULT_LOG_DAYS,
        try_get(aggregate_pattern.findall(text)),
        try_get(filter_pattern.findall(text)),
    )


def retrieve_logs(rater: Person, days: int = DEFAULT_LOG_DAYS,
                  filter: Optional[str] = None,
                  offset: int = None, limit: int = None) -> List[Interaction]:
    """retrieve the log of Interactions and return as a list"""
    since = timezone.now() - timedelta(days=days)
    qs = (Interaction.objects.filter(rater=rater, created__gte=since)
          .order_by("-created"))
    if filter is not None:
        qs = qs.filter(rating=filter)

    if limit is not None:
        offset = offset or 0
        qs = qs[offset:offset + limit]
    elif offset is not None:
        qs = qs[offset:]
    return list(qs)


def retrieve_aggregated_logs(rater: Person, days: int = DEFAULT_LOG_DAYS,
                             aggregate: Optional[str] = None,
                             filter: Optional[str] = None,
                             offset: int = None, limit: int = None) -> dict:
    """aggregate a list of interactions by person of period of time and return info on
    the interactions for that aggregation type. for example, return the number of
    positive and negative interations for each week in a time period"""
    interactions = retrieve_logs(rater=rater, days=days, filter=filter,
                                 offset=offset, limit=limit)

    def get_dd_int():
        return defaultdict(int)

    aggregated = defaultdict(get_dd_int)
    if aggregate == "person":
        for interaction in interactions:
            if interaction.rating == Interaction.POSITIVE:
                aggregated[interaction.ratee]["positive"] += 1
            elif interaction.rating == Interaction.NEGATIVE:
                aggregated[interaction.ratee]["negative"] += 1

    if aggregate == "time":
        if days < 14:
            delta = 1
        elif days < 60:
            delta = 7
        else:
            delta = 30

        interactions.sort(key=lambda x: x.created)
        first = interactions[0].created
        last = interactions[-1].created

        buckets = []
        current = first
        while current <= last:
            nxt = current + timedelta(days=delta)
            buckets.append((current, nxt))
            current = nxt
        for bucket in buckets:
            key = bucket[0].strftime("%d %b %Y")
            for interaction in interactions:
                if not (bucket[0] >= interaction.created < bucket[1]):
                    continue
                if interaction.rating == Interaction.POSITIVE:
                    aggregated[key]["positive"] += 1
                elif interaction.rating == Interaction.NEGATIVE:
                    aggregated[key]["negative"] += 1

    return aggregated


def clear_logs(rater_user_id: str) -> int:
    """clear the database of rater created Interactions"""
    person = Person.objects.get(user_id=rater_user_id)
    Interaction.objects.filter(rater=person).delete()
    return Interaction.objects.filter(rater=person).count()


def do_create(rater_user_id: str, text: str) -> int:
    tuples = text_to_interaction_tuples(text)
    created = create_interactions(rater_user_id, *tuples)
    return len(created)


def do_logs(rater_user_id: str, text: str, limit: int = 5) -> Union[list, dict]:
    log_request = parse_log_request_text(text)
    rater, _ = Person.objects.get_or_create(user_id=rater_user_id)
    if log_request[1] is None:
        return retrieve_logs(rater=rater, days=log_request[0], filter=log_request[2],
                             limit=limit)
    else:
        return retrieve_aggregated_logs(rater=rater, days=log_request[0],
                                        aggregate=log_request[1],
                                        filter=log_request[2], limit=limit)
