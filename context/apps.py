from django.apps import AppConfig


class ContextConfig(AppConfig):
    name = 'context'

    def ready(self):
        from context import signals
