from django.apps import AppConfig


class FeaturesConfig(AppConfig):
    name = 'features'

    def ready(self):
        import features.signals
