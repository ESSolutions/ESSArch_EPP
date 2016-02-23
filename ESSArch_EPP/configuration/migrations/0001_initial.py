# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import picklefield.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ArchivePolicy',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('PolicyID', models.CharField(unique=True, max_length=32, verbose_name=b'Policy ID')),
                ('PolicyName', models.CharField(max_length=255, verbose_name=b'Policy Name')),
                ('PolicyStat', models.IntegerField(default=0, verbose_name=b'Policy Status', choices=[(0, b'Disabled'), (1, b'Enabled')])),
                ('AISProjectName', models.CharField(max_length=255, verbose_name=b'AIS Policy Name', blank=True)),
                ('AISProjectID', models.CharField(max_length=255, verbose_name=b'AIS Policy ID', blank=True)),
                ('Mode', models.IntegerField(default=0, choices=[(0, b'Master'), (2, b'AIS')])),
                ('WaitProjectApproval', models.IntegerField(default=2, verbose_name=b'Wait for approval', choices=[(0, b'No'), (2, b'IngestRequest')])),
                ('ChecksumAlgorithm', models.IntegerField(default=1, verbose_name=b'Checksum algorithm', choices=[(1, b'MD5'), (2, b'SHA-256')])),
                ('ValidateChecksum', models.IntegerField(default=1, verbose_name=b'Validate checksum', choices=[(0, b'Disabled'), (1, b'Enabled')])),
                ('ValidateXML', models.IntegerField(default=1, verbose_name=b'Validate XML', choices=[(0, b'Disabled'), (1, b'Enabled')])),
                ('ManualControll', models.IntegerField(default=0, verbose_name=b'Manual Control', choices=[(0, b'Disabled'), (1, b'Enabled')])),
                ('AIPType', models.IntegerField(default=1, verbose_name=b'AIP type', choices=[(1, b'TAR')])),
                ('AIPpath', models.CharField(default=b'/ESSArch/work', max_length=255, verbose_name=b'Temp work directory')),
                ('PreIngestMetadata', models.IntegerField(default=0, verbose_name=b'Pre ingest metadata', choices=[(0, b'Disabled'), (1, b'RES')])),
                ('IngestMetadata', models.IntegerField(default=4, verbose_name=b'Ingest metadata', choices=[(1, b'METS'), (4, b'METS (eArd)')])),
                ('INFORMATIONCLASS', models.IntegerField(default=0, verbose_name=b'Information class', choices=[(0, b'0'), (1, b'1'), (2, b'2'), (3, b'3'), (4, b'4')])),
                ('IngestPath', models.CharField(default=b'/ESSArch/ingest', max_length=255, verbose_name=b'Ingest directory')),
                ('IngestDelete', models.IntegerField(default=1, verbose_name=b'Delete SIP after success to create AIP', choices=[(0, b'Disabled'), (1, b'Enabled')])),
            ],
            options={
                'ordering': ['PolicyName'],
            },
        ),
        migrations.CreateModel(
            name='DefaultValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('entity', models.CharField(unique=True, max_length=255)),
                ('value', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['entity'],
                'verbose_name': 'Default value',
            },
        ),
        migrations.CreateModel(
            name='ESSConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Name', models.CharField(max_length=255)),
                ('Value', models.CharField(max_length=255, blank=True)),
                ('Status', models.CharField(max_length=10, blank=True)),
            ],
            options={
                'db_table': 'ESSConfig',
                'verbose_name': 'Parameter (core)',
            },
        ),
        migrations.CreateModel(
            name='ESSProc',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Name', models.CharField(max_length=255)),
                ('Path', models.CharField(max_length=255)),
                ('LogFile', models.CharField(max_length=255)),
                ('expected_pids', models.IntegerField(default=1)),
                ('Time', models.CharField(max_length=4)),
                ('Status', models.CharField(max_length=10)),
                ('Run', models.CharField(max_length=10)),
                ('PID', models.IntegerField()),
                ('child_pids', picklefield.fields.PickledObjectField(null=True, editable=False)),
                ('Pause', models.IntegerField()),
                ('checked', models.DateTimeField(default=b'2014-01-01 00:01')),
                ('alarm', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'ESSProc',
                'verbose_name': 'Worker processes (core)',
            },
        ),
        migrations.CreateModel(
            name='IPParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('objid', models.CharField(unique=True, max_length=255)),
                ('label', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255)),
                ('createdate', models.CharField(max_length=255)),
                ('recordstatus', models.CharField(max_length=255)),
                ('deliverytype', models.CharField(max_length=255)),
                ('deliveryspecification', models.CharField(max_length=255)),
                ('submissionagreement', models.CharField(max_length=255)),
                ('previoussubmissionagreement', models.CharField(max_length=255)),
                ('datasubmissionsession', models.CharField(max_length=255)),
                ('packagenumber', models.CharField(max_length=255)),
                ('referencecode', models.CharField(max_length=255)),
                ('previousreferencecode', models.CharField(max_length=255)),
                ('appraisal', models.CharField(max_length=255)),
                ('accessrestrict', models.CharField(max_length=255)),
                ('archivist_organization', models.CharField(max_length=255)),
                ('archivist_organization_id', models.CharField(max_length=255)),
                ('archivist_organization_software', models.CharField(max_length=255)),
                ('archivist_organization_software_id', models.CharField(max_length=255)),
                ('creator_organization', models.CharField(max_length=255)),
                ('creator_organization_id', models.CharField(max_length=255)),
                ('creator_individual', models.CharField(max_length=255)),
                ('creator_individual_details', models.CharField(max_length=255)),
                ('creator_software', models.CharField(max_length=255)),
                ('creator_software_id', models.CharField(max_length=255)),
                ('editor_organization', models.CharField(max_length=255)),
                ('editor_organization_id', models.CharField(max_length=255)),
                ('preservation_organization', models.CharField(max_length=255)),
                ('preservation_organization_id', models.CharField(max_length=255)),
                ('preservation_organization_software', models.CharField(max_length=255)),
                ('preservation_organization_software_id', models.CharField(max_length=255)),
                ('startdate', models.CharField(max_length=255)),
                ('enddate', models.CharField(max_length=255)),
                ('aic_id', models.CharField(max_length=255)),
                ('informationclass', models.CharField(max_length=255)),
                ('projectname', models.CharField(max_length=255)),
                ('policyid', models.IntegerField(default=0)),
                ('receipt_email', models.CharField(max_length=255)),
                ('file_id', models.CharField(max_length=255)),
                ('file_name', models.CharField(max_length=255)),
                ('file_createdate', models.CharField(max_length=255)),
                ('file_mime_type', models.CharField(max_length=255)),
                ('file_format', models.CharField(max_length=255)),
                ('file_format_size', models.CharField(max_length=255)),
                ('file_type', models.CharField(max_length=255)),
                ('file_checksum', models.CharField(max_length=255)),
                ('file_checksum_type', models.CharField(max_length=255)),
                ('file_transform_type', models.CharField(max_length=255)),
                ('file_transform_key', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['type'],
                'verbose_name': 'Default values for IP parameter',
            },
        ),
        migrations.CreateModel(
            name='Parameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('entity', models.CharField(unique=True, max_length=255)),
                ('value', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['entity'],
            },
        ),
        migrations.CreateModel(
            name='Path',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('entity', models.CharField(unique=True, max_length=255)),
                ('value', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['entity'],
            },
        ),
        migrations.CreateModel(
            name='SchemaProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('entity', models.CharField(unique=True, max_length=255)),
                ('value', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['entity'],
                'verbose_name': 'XML schema',
            },
        ),
        migrations.CreateModel(
            name='StorageMethod',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name=b'Name', blank=True)),
                ('status', models.IntegerField(default=0, verbose_name=b'Storage method status', choices=[(0, b'Disabled'), (1, b'Enabled')])),
                ('type', models.IntegerField(default=200, verbose_name=b'Type', choices=[(200, b'DISK'), (300, b'TAPE'), (400, b'CAS')])),
                ('archivepolicy', models.ForeignKey(to='configuration.ArchivePolicy')),
            ],
            options={
                'ordering': ['name'],
            },                               
        ),
        migrations.CreateModel(
            name='StorageTarget',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name=b'Name', blank=True)),
                ('status', models.IntegerField(default=0, verbose_name=b'Storage target status', choices=[(0, b'Disabled'), (1, b'Enabled'), (2, b'ReadOnly'), (3, b'Migrate')])),
                ('storagemethod', models.ForeignKey(to='configuration.StorageMethod')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Target',
            },
        ),
        migrations.CreateModel(
            name='StorageTargets',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name=b'Name')),
                ('status', models.IntegerField(default=1, verbose_name=b'Storage target status', choices=[(0, b'Disabled'), (1, b'Enabled')])),
                ('type', models.IntegerField(default=200, verbose_name=b'Type', choices=[(200, b'DISK'), (301, b'IBM-LTO1'), (302, b'IBM-LTO2'), (303, b'IBM-LTO3'), (304, b'IBM-LTO4'), (305, b'IBM-LTO5'), (306, b'IBM-LTO6'), (325, b'HP-LTO5'), (326, b'HP-LTO6'), (401, b'HDFS'), (402, b'HDFS-REST')])),
                ('format', models.IntegerField(default=103, verbose_name=b'Format', choices=[(103, b'103 (AIC support)'), (102, b'102 (Media label)'), (101, b'101 (Old read only)'), (100, b'100 (Old read only)')])),
                ('blocksize', models.BigIntegerField(default=1024, verbose_name=b'BlockSize (tape)', choices=[(128, b'64K'), (250, b'125K'), (256, b'128K'), (512, b'256K'), (1024, b'512K'), (2048, b'1024K')])),
                ('maxCapacity', models.BigIntegerField(default=0, verbose_name=b'Max capacity (0=Disabled)')),
                ('minChunkSize', models.BigIntegerField(default=0, verbose_name=b'Min chunk size', choices=[(0, b'Disabled'), (1048576, b'1 MByte'), (1073741824, b'1 GByte'), (53687091201, b'5 GByte'), (10737418240, b'10 GByte'), (107374182400, b'100 GByte'), (214748364800, b'200 GByte'), (322122547200, b'300 GByte'), (429496729600, b'400 GByte'), (536870912000, b'500 GByte')])),
                ('minContainerSize', models.BigIntegerField(default=0, verbose_name=b'Min container size (0=Disabled)', choices=[(0, b'Disabled')])),
                ('minCapacityWarning', models.BigIntegerField(default=0, verbose_name=b'Min capacity warning (0=Disabled)')),
                ('remote_server', models.CharField(max_length=255, verbose_name=b'Remote server (https://hostname,user,password)', blank=True)),
                ('master_server', models.CharField(max_length=255, verbose_name=b'Master server (https://hostname,user,password)', blank=True)),
                ('target', models.CharField(max_length=255, verbose_name=b'Target (URL, path or barcodeprefix)')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Storage Target',
            },
        ),
        migrations.AddField(
            model_name='storagetarget',
            name='target',
            field=models.ForeignKey(to='configuration.StorageTargets'),
        ),
    ]
