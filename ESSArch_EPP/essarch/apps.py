from django.apps import AppConfig

class ESSArchAppConfig(AppConfig):
    name = 'essarch'
    verbose_name = "essarch"

    def ready(self):
        import essarch.signals # register the signals