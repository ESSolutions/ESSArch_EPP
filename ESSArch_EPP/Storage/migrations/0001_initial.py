# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuid
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0001_initial'),
        ('essarch', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IOQueue',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('ReqType', models.IntegerField(choices=[(10, b'Write to tape'), (15, b'Write to disk'), (20, b'Read from tape'), (25, b'Read from disk'), (41, b'Write to HDFS'), (42, b'Read from HDFS'), (43, b'Write to HDFS-REST'), (44, b'Read from HDFS-REST')])),
                ('ReqPurpose', models.CharField(max_length=255, blank=True)),
                ('user', models.CharField(max_length=45)),
                ('ObjectPath', models.CharField(max_length=256, blank=True)),
                ('WriteSize', models.BigIntegerField(null=True, blank=True)),
                ('result', picklefield.fields.PickledObjectField(editable=False, blank=True)),
                ('Status', models.IntegerField(default=0, blank=True, choices=[(0, b'Pending'), (2, b'Initiate'), (5, b'Progress'), (20, b'Success'), (100, b'FAIL')])),
                ('task_id', models.CharField(max_length=36, blank=True)),
                ('posted', models.DateTimeField(auto_now_add=True)),
                ('remote_status', models.IntegerField(default=0, blank=True, choices=[(0, b'Pending'), (2, b'Initiate'), (5, b'Transfer'), (20, b'Success'), (100, b'FAIL')])),
                ('transfer_task_id', models.CharField(max_length=36, blank=True)),
                ('accessqueue', models.ForeignKey(blank=True, to='essarch.AccessQueue', null=True)),
                ('archiveobject', models.ForeignKey(to_field=b'ObjectUUID', blank=True, to='essarch.ArchiveObject', null=True)),
            ],
            options={
                'permissions': (('list_IOQueue', 'Can list IOQueue'),),
            },
        ),
        migrations.CreateModel(
            name='storage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('contentLocationType', models.IntegerField(choices=[(200, b'DISK'), (300, b'TAPE'), (400, b'CAS')])),
                ('contentLocationValue', models.CharField(max_length=255)),
                ('LocalDBdatetime', models.DateTimeField(null=True)),
                ('ExtDBdatetime', models.DateTimeField(null=True)),
                ('archiveobject', models.ForeignKey(related_name='Storage_set', to='essarch.ArchiveObject', to_field=b'ObjectUUID')),
            ],
            options={
                'permissions': (('list_storage', 'Can list storage'),),
            },
        ),
        migrations.CreateModel(
            name='storageMedium',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('storageMediumUUID', models.CharField(unique=True, max_length=36)),
                ('storageMedium', models.IntegerField(choices=[(200, b'DISK'), (301, b'IBM-LTO1'), (302, b'IBM-LTO2'), (303, b'IBM-LTO3'), (304, b'IBM-LTO4'), (305, b'IBM-LTO5'), (306, b'IBM-LTO6'), (325, b'HP-LTO5'), (326, b'HP-LTO6'), (401, b'HDFS'), (402, b'HDFS-REST')])),
                ('storageMediumID', models.CharField(unique=True, max_length=255)),
                ('storageMediumDate', models.DateTimeField()),
                ('storageMediumLocation', models.CharField(max_length=255)),
                ('storageMediumLocationStatus', models.IntegerField(choices=[(10, b'Delivered'), (20, b'Received'), (30, b'Placed'), (40, b'Collected'), (50, b'Robot')])),
                ('storageMediumBlockSize', models.IntegerField(choices=[(128, b'64K'), (250, b'125K'), (256, b'128K'), (512, b'256K'), (1024, b'512K'), (2048, b'1024K')])),
                ('storageMediumUsedCapacity', models.BigIntegerField()),
                ('storageMediumStatus', models.IntegerField(choices=[(0, b'Inactive'), (20, b'Write'), (30, b'Full'), (100, b'FAIL')])),
                ('storageMediumFormat', models.IntegerField(choices=[(103, b'103 (AIC support)'), (102, b'102 (Media label)'), (101, b'101 (Old read only)'), (100, b'100 (Old read only)')])),
                ('storageMediumMounts', models.IntegerField()),
                ('linkingAgentIdentifierValue', models.CharField(max_length=255)),
                ('CreateDate', models.DateTimeField(null=True)),
                ('CreateAgentIdentifierValue', models.CharField(max_length=255)),
                ('LocalDBdatetime', models.DateTimeField(null=True)),
                ('ExtDBdatetime', models.DateTimeField(null=True)),
                ('storagetarget', models.ForeignKey(to='configuration.StorageTargets')),
            ],
            options={
                'permissions': (('list_storageMedium', 'Can list storageMedium'),),
            },
        ),
        migrations.AddField(
            model_name='storage',
            name='storagemedium',
            field=models.ForeignKey(to='Storage.storageMedium'),
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
