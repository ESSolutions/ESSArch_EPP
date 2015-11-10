# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('essarch', '0001_initial'),
        ('configuration', '0001_initial'),
        ('Storage', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='storage',
            name='archiveobject',
            field=models.ForeignKey(related_name='Storage_set', to='essarch.ArchiveObject', to_field=b'ObjectUUID'),
        ),
        migrations.AddField(
            model_name='storage',
            name='storagemedium',
            field=models.ForeignKey(to='Storage.storageMedium'),
        ),
        migrations.AddField(
            model_name='ioqueue',
            name='accessqueue',
            field=models.ForeignKey(blank=True, to='essarch.AccessQueue', null=True),
        ),
        migrations.AddField(
            model_name='ioqueue',
            name='archiveobject',
            field=models.ForeignKey(to_field=b'ObjectUUID', blank=True, to='essarch.ArchiveObject', null=True),
        ),
        migrations.AddField(
            model_name='ioqueue',
            name='storage',
            field=models.ForeignKey(blank=True, to='Storage.storage', null=True),
        ),
        migrations.AddField(
            model_name='ioqueue',
            name='storagemedium',
            field=models.ForeignKey(blank=True, to='Storage.storageMedium', null=True),
        ),
        migrations.AddField(
            model_name='ioqueue',
            name='storagemethod',
            field=models.ForeignKey(blank=True, to='configuration.StorageMethod', null=True),
        ),
        migrations.AddField(
            model_name='ioqueue',
            name='storagemethodtarget',
            field=models.ForeignKey(blank=True, to='configuration.StorageTarget', null=True),
        ),
        migrations.AddField(
            model_name='ioqueue',
            name='storagetarget',
            field=models.ForeignKey(blank=True, to='configuration.StorageTargets', null=True),
        ),
    ]
