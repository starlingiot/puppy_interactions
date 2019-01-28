import uuid
from datetime import timedelta
from random import choice, randint
from unittest import mock
from puppy_interactions.interactions.help_message import HELP_MESSAGE

from django.test import TestCase, Client
from django.urls import reverse_lazy
from django.utils import timezone

from puppy_interactions.interactions.models import Interaction, Person

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


class InteractionViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.client = Client()
        cls.user_id = "U2147483697"

        rater = Person.objects.create(user_id="R2385729")
        rando = Person.objects.create(user_id="F2385729")
        ratings = [Interaction.POSITIVE, Interaction.NEGATIVE]

        persons = [Person(user_id=f"U{randint(100000, 999999)}") for num in range(25)]
        persons = Person.objects.bulk_create(persons)

        for num in reversed(range(90)):
            testtime = timezone.now() - timedelta(days=num)
            with mock.patch('django.utils.timezone.now') as mock_now:
                mock_now.return_value = testtime
                Interaction.objects.create(conversation=uuid.uuid4(), rater=rater,
                                           ratee=choice(persons),
                                           rating=choice(ratings))
                Interaction.objects.create(conversation=uuid.uuid4(), rater=rando,
                                           ratee=choice(persons),
                                           rating=choice(ratings))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def make_payload(self, text):
        """create a sample payload with desired text value"""
        return {"token": "gIkuvaNzQIHg97ATvDxqgjtO",
                "team_id": "T0001",
                "team_domain": "example",
                "enterprise_id": "E0001",
                "enterprise_name": "Globular%20Construct%20Inc",
                "channel_id": "C2147483705",
                "channel_name": "test",
                "user_id": f"{self.user_id}",
                "user_name": "Steve",
                "command": "/interactions",
                "text": text,
                "response_url": "https://hooks.slack.com/commands/1234/5678",
                "trigger_id": "13345224609.738474920.8088930838d88f008e0}"}

    def test_create(self):
        """test returns 200 and creates Interactions"""
        new_count = Interaction.objects.count()
        response = self.client.post(
            path=reverse_lazy("interactions"),
            data=self.make_payload("Joseph Curtin + <@U23787> - <@U298333> + Trisha -")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Interaction.objects.count(), new_count + 4)

    def test_logs(self):
        """test returns 200 and list of attachments"""
        response = self.client.post(
            path=reverse_lazy("interactions"),
            data=self.make_payload("")
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIsInstance(json_data.get("attachments"), list)

    def test_logs_aggr(self):
        """test returns 200 and list of attachments"""
        response = self.client.post(
            path=reverse_lazy("interactions"),
            data=self.make_payload("90 person")
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIsInstance(json_data.get("attachments"), list)

    def test_clear(self):
        """test return 200 and removes raters Interactions"""
        response = self.client.post(
            path=reverse_lazy("interactions"),
            data=self.make_payload("clear")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Interaction.objects.filter(rater__user_id=f"<@{self.user_id}>").count(), 0
        )

    def test_help(self):
        response = self.client.post(
            path=reverse_lazy("interactions"),
            data=self.make_payload("help")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), HELP_MESSAGE)
