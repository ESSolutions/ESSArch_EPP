from django.apps import AppConfig


class StorageConfig(AppConfig):
    name = 'storage'
    label = 'epp_storage'

    def ready(self):
        import storage.signals  # noqa
