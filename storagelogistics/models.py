from django.db import models

# Create your models here.
class permission(models.Model):
    class Meta:
        permissions = (
            ("StorageLogistics", "StorageLogistics"),
        )
