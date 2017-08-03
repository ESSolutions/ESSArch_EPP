from django.apps import AppConfig


class StorageConfig(AppConfig):
    name = 'ESSArch_Core.storage'
    verbose_name = 'Storage'

    def ready(self):
        import storage.signals  # noqa