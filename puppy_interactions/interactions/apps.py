from django.apps import AppConfig


class InteractionsAppConfig(AppConfig):

    name = "puppy_interactions.interactions"

    verbose_name = "PuPPY Interactions"

    def ready(self):
        pass
