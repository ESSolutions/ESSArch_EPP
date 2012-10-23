from django.db import models

# Create your models here.
class permission(models.Model):
    class Meta:
        permissions = (
            ("ESSArch_Marieberg", "site Marieberg"),
            ("ESSArch_MKC", "site MKC"),
            ("ESSArch_SVAR", "site SVAR"),
            ("ESSArch_HLA", "site HLA"),
            ("ESSArch_Globen", "site Globen"),
            ("essadministrate", "ESSArch admin "),
            ("essaccess", "ESSArch access"),
            ("essingest", "ESSArch ingest"),
            ("infoclass_1", "Information Class 1"),
            ("infoclass_2", "Information Class 2"),
            ("infoclass_3", "Information Class 3"),
            ("infoclass_4", "Information Class 4"),
        )
