# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import api.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TmpWorkareaUpload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('upload_id', models.CharField(default=api.models.generate_upload_id, unique=True, max_length=32, editable=False)),
                ('filename', models.CharField(max_length=255)),
                ('offset', models.BigIntegerField(default=0)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('status', models.PositiveSmallIntegerField(default=1, choices=[(1, 'Uploading'), (2, 'Complete')])),
                ('completed_on', models.DateTimeField(null=True, blank=True)),
                ('file', models.FileField(storage=api.models.TmpWorkarea_storage(), max_length=255, upload_to=api.models.TmpWorkarea_filename)),
                ('user', models.ForeignKey(related_name='chunked_uploads', blank=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
