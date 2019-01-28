from django.db import models
import uuid


class InteractionBaseModel(models.Model):
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created = models.DateTimeField(auto_now_add=True)

    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Person(InteractionBaseModel):
    # Slack `user-id` or string representation (for interactions without @notation)
    user_id = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        if self.display_name != "":
            return self.display_name
        else:
            return self.user_id


class Interaction(InteractionBaseModel):
    """
    models an interaction between two people. it can be ranked as a `+` or `-`.

    one person can have many interactions within a conversation. for example, in a
    3-person interaction (conversation1).
      *  personA -> personB = conversation1.interaction1
      *  personA -> personC = conversation1.interaction2
      *  personB -> personC = conversation1.interaction3
      *  personC -> personA = conversation1.interaction4
      *  ...

    because we can't explicitly link conversations reported by different people, we
    will see multiple conversation UUIDs for a single conversation. that means a single
    conversation may present as multiple conversations without some temporal- and user-
    based heuristics.
    """

    # ensure this is set the same for all interactions in the conversation
    conversation = models.UUIDField(default=uuid.uuid4)

    rater = models.ForeignKey('interactions.Person', on_delete=models.PROTECT,
                              related_name='rater_interactions')

    ratee = models.ForeignKey('interactions.Person', on_delete=models.PROTECT,
                              related_name='ratee_interactions', null=True)

    POSITIVE = "+"
    NEGATIVE = "-"
    RATING_CHOICES = (
        (POSITIVE, "Positive"),
        (NEGATIVE, "Negative"),
    )
    rating = models.CharField(max_length=1, choices=RATING_CHOICES)

    @staticmethod
    def map_to_icon(rating: str) -> str:
        """return a Slack emoji from a rating"""
        m = {Interaction.POSITIVE: ":slightly_smiling_face:",
             Interaction.NEGATIVE: ":white_frowning_face:"}
        return m.get(rating, ":grey_question:")

    def __str__(self):
        icon = self.map_to_icon(self.rating)
        return f"*{self.ratee}*\t{self.created.strftime('%d %b %Y')}\t*{icon}*"
