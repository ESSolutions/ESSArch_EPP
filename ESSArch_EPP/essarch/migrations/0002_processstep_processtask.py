# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import picklefield.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('essarch', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProcessStep',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=256, blank=True)),
                ('type', models.IntegerField(null=True, choices=[(0, b'Receive new object'), (5, b'The object is ready to remodel'), (9, b'New object stable'), (10, b"Object don't exist in AIS"), (11, b"Object don't have any projectcode in AIS"), (12, b"Object don't have any local policy"), (13, b'Object already have an AIP!'), (14, b'Object is not active!'), (19, b'Object got a policy'), (20, b'Object not updated from AIS'), (21, b'Object not accepted in AIS'), (24, b'Object accepted in AIS'), (25, b'SIP validate'), (26, b'SIP validate failed'), (29, b'SIP validate OK'), (30, b'Create AIP package'), (31, b'AIP create failed'), (39, b'AIP created OK'), (40, b'Create package checksum'), (49, b'AIP checksum created OK'), (50, b'AIP validate'), (51, b'AIP validate failed'), (59, b'AIP validate OK'), (60, b'Try to remove IngestObject'), (61, b'Failed to remove IngestObject'), (69, b'Remove OK of IngestObject'), (1000, b'Write AIP to longterm storage'), (1001, b'Fail to write AIP'), (1002, b'No empty media available'), (1003, b'Problem to mount media'), (1004, b'Failed to verify tape after full write'), (1500, b'Remote AIP'), (1999, b'Write AIP OK'), (2000, b'Try to remove temp AIP object'), (2001, b'Failed to remove temp AIP object'), (2009, b'Remove temp AIP object OK'), (3000, b'Archived'), (5000, b'ControlArea'), (5100, b'WorkArea'), (9999, b'Deleted')])),
                ('user', models.CharField(max_length=45)),
                ('result', picklefield.fields.PickledObjectField(editable=False, blank=True)),
                ('status', models.IntegerField(default=0, blank=True, choices=[(0, b'Pending'), (2, b'Initiate'), (5, b'Progress'), (20, b'Success'), (100, b'FAIL')])),
                ('posted', models.DateTimeField(auto_now_add=True)),
                ('progress', models.IntegerField(default=0, blank=True)),
                ('hidden', models.BooleanField(default=False)),
                ('archiveobject', models.ForeignKey(to_field=b'ObjectUUID', blank=True, to='essarch.ArchiveObject', null=True)),
            ],
            options={
                'db_table': 'ProcessStep',
            },
        ),
        migrations.CreateModel(
            name='ProcessTask',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=256, blank=True)),
                ('task_id', models.CharField(unique=True, max_length=255, verbose_name='task id')),
                ('status', models.CharField(default=b'PENDING', max_length=50, verbose_name='state', choices=[(b'RECEIVED', b'RECEIVED'), (b'RETRY', b'RETRY'), (b'REVOKED', b'REVOKED'), (b'SUCCESS', b'SUCCESS'), (b'STARTED', b'STARTED'), (b'FAILURE', b'FAILURE'), (b'PENDING', b'PENDING')])),
                ('result', picklefield.fields.PickledObjectField(default=None, null=True, editable=False)),
                ('date_done', models.DateTimeField(auto_now=True, verbose_name='done at')),
                ('traceback', models.TextField(null=True, verbose_name='traceback', blank=True)),
                ('hidden', models.BooleanField(default=False, db_index=True, editable=False)),
                ('meta', picklefield.fields.PickledObjectField(default=None, null=True, editable=False)),
                ('progress', models.IntegerField(default=0, blank=True)),
                ('processstep', models.ForeignKey(blank=True, to='essarch.ProcessStep', null=True)),
            ],
            options={
                'db_table': 'ProcessTask',
            },
        ),
    ]
