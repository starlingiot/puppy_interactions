import uuid
from datetime import timedelta
from random import choice, randint
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from puppy_interactions.interactions.exceptions import (
    UnrecognizedCommandException, CheaterException
)
from puppy_interactions.interactions.models import Interaction, Person
from puppy_interactions.interactions.utils import (
    DEFAULT_LOG_DAYS, parse_webhook_text, create_interactions,
    text_to_interaction_tuples, parse_log_request_text, retrieve_logs,
    retrieve_aggregated_logs, clear_logs
)


class CommandTextParseTests(TestCase):
    def test_parse_single_interaction_id(self):
        """test parsing a single interaction string using user_id"""
        text = "<@U2398577> +"
        self.assertEqual(parse_webhook_text(text), "create")

    def test_parse_multiple_interaction_id(self):
        """test parsing a single interaction string using user_id"""
        text = "<@U2398577> + <@U2498577> - <@U2598577> +"
        self.assertEqual(parse_webhook_text(text), "create")

    def test_parse_single_interaction_name(self):
        """test parsing a single interaction string using raw name"""
        text = "Joseph Curtin +"
        self.assertEqual(parse_webhook_text(text), "create")

    def test_parse_multiple_mixed_interaction(self):
        """test parsing multiple interaction string with mixed user_id and raw name"""
        text = "Joseph Curtin + <@U23787> - <@U298333> + Trisha -"
        self.assertEqual(parse_webhook_text(text), "create")

    def test_parse_get_log(self):
        """test parsing getting a log"""
        text = ""
        self.assertEqual(parse_webhook_text(text), "logs")

    def test_parse_get_log_filtered(self):
        """test parsing getting a log filtering for positive or negative"""
        texts = ["+", "-", " -", " +", "+ ", "- "]
        for text in texts:
            self.assertEqual(parse_webhook_text(text), "logs")

    def test_parse_get_log_w_time(self):
        """test parsing getting a log with time argument"""
        text = "90"
        self.assertEqual(parse_webhook_text(text), "logs")

    def test_parse_get_log_w_person_aggr(self):
        """test parsing getting a log with person aggregation arg"""
        text = "person"
        self.assertEqual(parse_webhook_text(text), "logs")

    def test_parse_get_log_w_time_aggr(self):
        """test parsing getting a log with time arg and time aggregation arg"""
        text = "time"
        self.assertEqual(parse_webhook_text(text), "logs")

    def test_parse_get_log_w_time_and_time_aggr(self):
        """test parsing getting a log with time arg and time aggregation arg"""
        text = "90 time"
        self.assertEqual(parse_webhook_text(text), "logs")

    def test_parse_get_log_w_time_and_person_aggr(self):
        """test parsing getting a log with time arg and time aggregation arg"""
        text = "90 person"
        self.assertEqual(parse_webhook_text(text), "logs")

    def test_all_three_log_params(self):
        """test parsing getting a log with all three possible params"""
        text = "90 time -"
        self.assertEqual(parse_webhook_text(text), "logs")

    def test_parse_clear(self):
        """test parsing the clear command"""
        text = "clear"
        self.assertEqual(parse_webhook_text(text), "clear")

    def test_parse_help(self):
        """test parsing the help command"""
        text = "help"
        self.assertEqual(parse_webhook_text(text), "help")

    def test_various_nonconforming_strings(self):
        """test some strings that should not conform to any action"""
        texts = [
            ";sadlfkjs;ldfj", "+ @U23984", "Joseph Curtin person", "help clear",
            "clear help"
        ]
        for text in texts:
            self.assertRaises(UnrecognizedCommandException, parse_webhook_text, text)


class TextToInteractionTuplesTests(TestCase):
    def test_returns_list(self):
        self.assertIsInstance(text_to_interaction_tuples(""), list)

    def test_single_interaction(self):
        """test a single interaction for user_id and raw name each"""
        text = "<@U2398577> +"
        self.assertEqual(text_to_interaction_tuples(text),
                         [("@U2398577", "+")])

    def test_multiple_interactions_mixed(self):
        """test multiple interactions with user_id and raw name"""
        text = "<@U2398577> + <@U2398578> - Trisha + <@U2398578>-"
        out = [("@U2398577", "+"), ("@U2398578", "-"),
               ("Trisha", "+"), ("@U2398578", "-")]
        self.assertEqual(text_to_interaction_tuples(text), out)


class CreateInteractionsTests(TestCase):
    def setUp(self):
        self.rater_user_id = f"@R{randint(100000, 999999)}"

    def test_returns_list_of_interactions_single(self):
        """test that the util returns a list of Interaction objects of proper size"""
        results = create_interactions(
            self.rater_user_id, (f"@U{randint(100000, 999999)}", choice(["+", "-"]))
        )
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], Interaction)

    def test_returns_list_of_interactions_multiple(self):
        """test that the util returns a list of Interaction objects of proper size"""
        total_num_expected = 5
        interaction_tuples = [(f"@U{randint(100000, 999999)}", choice(["+", "-"]))
                              for num in range(total_num_expected)]
        results = create_interactions(self.rater_user_id, *interaction_tuples)
        self.assertEqual(len(results), total_num_expected)
        for result in results:
            self.assertIsInstance(result, Interaction)

    def test_raises_w_improper_rating(self):
        """test that the util raises an exception with nonexistent rating choice"""
        self.assertRaises(TypeError, create_interactions,
                          self.rater_user_id, ("Trisha Jambolo", "*"))

    def test_single_interactions_different_conversation(self):
        """test that single interactions created with separate calls have unique
        conversations for same rater"""
        results1 = create_interactions(
            self.rater_user_id, (f"<@U{randint(100000, 999999)}>", choice(["+", "-"]))
        )
        results2 = create_interactions(
            self.rater_user_id, (f"<@U{randint(100000, 999999)}>", choice(["+", "-"]))
        )
        self.assertNotEqual(results1[0].conversation, results2[0].conversation)

    def test_multiple_interactions_share_conversation(self):
        """test that multiple interactions created with one call share a conversation"""
        total_num_expected = 5
        interaction_tuples = [(f"<@U{randint(100000, 999999)}>", choice(["+", "-"]))
                              for num in range(total_num_expected)]
        results = create_interactions(self.rater_user_id, *interaction_tuples)
        conversations = set([result.conversation for result in results])
        self.assertEqual(len(conversations), 1)

    def test_cant_rate_self(self):
        """test that a Person cannot rate themselves explicitly"""
        self.assertRaises(CheaterException, create_interactions, self.rater_user_id,
                          (self.rater_user_id, "+"))


class ParseLogRequestTextTests(TestCase):
    def test_no_addl_text(self):
        """test defaults with no command text"""
        text = ""
        self.assertEqual(parse_log_request_text(text), (DEFAULT_LOG_DAYS, None, None))

    def test_days(self):
        """test for days recognition"""
        text = "60"
        self.assertEqual(parse_log_request_text(text), (60, None, None))

    def test_aggregates(self):
        """test for aggregate recognition"""
        texts = ["person", "time"]
        for text in texts:
            self.assertEqual(parse_log_request_text(text),
                             (DEFAULT_LOG_DAYS, text, None))

    def test_filters(self):
        """test for filter recognition"""
        texts = [Interaction.POSITIVE, Interaction.NEGATIVE]
        for text in texts:
            self.assertEqual(parse_log_request_text(text),
                             (DEFAULT_LOG_DAYS, None, text))

    def test_two(self):
        """test combinations of two args to parse"""
        texts = [{"days": 60, "aggregate": None, "filter": Interaction.NEGATIVE},
                 {"days": None, "aggregate": "time", "filter": Interaction.POSITIVE},
                 {"days": 45, "aggregate": "person", "filter": None}]

        for text in texts:
            values = [str(v) for v in text.values() if v is not None]
            parse_str = " ".join(values)
            self.assertEqual(parse_log_request_text(parse_str),
                             (text["days"] or DEFAULT_LOG_DAYS, text["aggregate"],
                              text["filter"]))

    def test_all_three(self):
        """test parsing all three"""
        texts = [{"days": 60, "aggregate": "time", "filter": Interaction.NEGATIVE},
                 {"days": 7, "aggregate": "time", "filter": Interaction.POSITIVE},
                 {"days": 45, "aggregate": "person", "filter": Interaction.POSITIVE}]

        for text in texts:
            values = [str(v) for v in text.values() if v is not None]
            parse_str = " ".join(values)
            self.assertEqual(parse_log_request_text(parse_str),
                             (text["days"], text["aggregate"], text["filter"]))


class RetrieveBaseTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.rater = Person.objects.create(user_id="R2385729")
        faker = Person.objects.create(user_id="F2385729")
        ratings = [Interaction.POSITIVE, Interaction.NEGATIVE]

        persons = [Person(user_id=f"U{randint(100000, 999999)}") for num in range(25)]
        persons = Person.objects.bulk_create(persons)

        for num in reversed(range(90)):
            testtime = timezone.now() - timedelta(days=num)
            with mock.patch('django.utils.timezone.now') as mock_now:
                mock_now.return_value = testtime
                Interaction.objects.create(conversation=uuid.uuid4(), rater=cls.rater,
                                           ratee=choice(persons),
                                           rating=choice(ratings))
                Interaction.objects.create(conversation=uuid.uuid4(), rater=faker,
                                           ratee=choice(persons),
                                           rating=choice(ratings))

        cls.rater_logs = retrieve_logs(cls.rater, 7)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()


class RetrieveLogsTests(RetrieveBaseTests):
    def test_returns_list(self):
        """test that the util returns a list of Interactions"""
        self.assertIsInstance(self.rater_logs, list)
        for item in self.rater_logs:
            self.assertIsInstance(item, Interaction)

    def test_offset(self):
        """test that offset does just that"""
        offset = 10
        logs1 = retrieve_logs(self.rater)
        logs2 = retrieve_logs(self.rater, offset=offset)
        self.assertEqual(len(logs1), len(logs2) + offset)

    def test_limit(self):
        """test that limit does just that"""
        logs = retrieve_logs(self.rater, limit=5)
        self.assertEqual(len(logs), 5)

    def test_rater_in_all_interactions(self):
        """test we are only returning Interactions created by rater"""
        for item in self.rater_logs:
            self.assertEqual(item.rater, self.rater)

    def test_various_day_values(self):
        """test day values return proper amount of results"""
        test_days = [7, 30, 60, 90]
        for days in test_days:
            self.assertEqual(len(retrieve_logs(self.rater, days=days)),
                             Interaction.objects.filter(
                                 rater=self.rater,
                                 created__gte=timezone.now() - timedelta(days=days),
                             ).count())

    def test_filter_by_rating(self):
        """test that filters do indeed filter by rating"""
        logs = retrieve_logs(self.rater, filter=Interaction.POSITIVE)
        for log in logs:
            self.assertEqual(log.rating, Interaction.POSITIVE)

    def test_days_w_filter(self):
        """test days and filter together"""
        logs = retrieve_logs(self.rater, days=45, filter=Interaction.NEGATIVE)
        count = Interaction.objects.filter(
            rater=self.rater,
            created__gte=timezone.now() - timedelta(days=45),
            rating=Interaction.NEGATIVE
        ).count()
        self.assertEqual(len(logs), count)
        for log in logs:
            self.assertEqual(log.rating, Interaction.NEGATIVE)


class RetrieveAggregatedLogsTests(RetrieveBaseTests):
    def test_aggregate_by_person(self):
        """test aggregate by person does indeed do that"""
        logs = retrieve_aggregated_logs(self.rater, aggregate="person")
        self.assertIsInstance(logs, dict)
        for key, value in logs.items():
            self.assertIsInstance(key, Person)
            self.assertIsInstance(value, dict)

    def test_aggregate_by_time(self):
        """test that time aggregation returns proper aggregations"""
        logs = retrieve_aggregated_logs(self.rater, aggregate="time")
        self.assertIsInstance(logs, dict)
        for key, value in logs.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, dict)


class ClearLogTests(TestCase):
    def setUp(self):
        self.rater_id = f"@R{randint(100000, 999999)}"
        for num in range(20):
            create_interactions(
                self.rater_id,
                (f"@U{randint(100000, 999999)}",
                 choice([Interaction.POSITIVE, Interaction.NEGATIVE]))
            )
        for num in range(20):
            create_interactions(
                f"@U{randint(100000, 999999)}",
                (self.rater_id,
                 choice([Interaction.POSITIVE, Interaction.NEGATIVE]))
            )

    def test_leaves_no_interactions_as_rater(self):
        """test that the clear util removes all Interactions as rater"""
        clear_logs(self.rater_id)
        self.assertEqual(
            Interaction.objects.filter(rater__user_id=self.rater_id).count(), 0
        )

    def test_keeps_person_obj(self):
        """test that Person object still remains"""
        clear_logs(self.rater_id)
        self.assertTrue(Person.objects.filter(user_id=self.rater_id).exists())

    def test_keeps_interactions_as_ratee(self):
        """test that Interactions as ratee still remain"""
        clear_logs(self.rater_id)
        self.assertEqual(
            Interaction.objects.filter(ratee__user_id=self.rater_id).count(), 20
        )
