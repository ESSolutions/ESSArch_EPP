# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'LogEvent'
        db.create_table('configuration_logevent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('eventType', self.gf('django.db.models.fields.IntegerField')(default=0, unique=True)),
            ('eventDetail', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('configuration', ['LogEvent'])

        # Adding model 'Parameter'
        db.create_table('configuration_parameter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('entity', self.gf('django.db.models.fields.CharField')(unique=True, max_length=60)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=70)),
        ))
        db.send_create_signal('configuration', ['Parameter'])

        # Adding model 'Path'
        db.create_table('configuration_path', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('entity', self.gf('django.db.models.fields.CharField')(unique=True, max_length=60)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=70)),
        ))
        db.send_create_signal('configuration', ['Path'])

        # Adding model 'SchemaProfile'
        db.create_table('configuration_schemaprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('entity', self.gf('django.db.models.fields.CharField')(unique=True, max_length=60)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=70)),
        ))
        db.send_create_signal('configuration', ['SchemaProfile'])

        # Adding model 'IPParameter'
        db.create_table('configuration_ipparameter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('objid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('createdate', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('recordstatus', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('deliverytype', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('deliveryspecification', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('submissionagreement', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('previoussubmissionagreement', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('datasubmissionsession', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('packagenumber', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('referencecode', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('previousreferencecode', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('appraisal', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('accessrestrict', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('archivist_organization', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('archivist_organization_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('archivist_organization_software', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('archivist_organization_software_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('creator_organization', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('creator_organization_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('creator_individual', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('creator_individual_details', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('creator_software', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('creator_software_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('editor_organization', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('editor_organization_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('preservation_organization', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('preservation_organization_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('preservation_organization_software', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('preservation_organization_software_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('startdate', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('enddate', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('aic_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('informationclass', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('projectname', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('policyid', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('receipt_email', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_createdate', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_mime_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_format', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_format_size', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_checksum', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_checksum_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_transform_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_transform_key', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('configuration', ['IPParameter'])

        # Adding model 'ESSArchPolicy'
        db.create_table('ESSArchPolicy', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('PolicyName', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('PolicyID', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('PolicyStat', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('AISProjectName', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('AISProjectID', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('Mode', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('WaitProjectApproval', self.gf('django.db.models.fields.IntegerField')(default=2)),
            ('ChecksumAlgorithm', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('ValidateChecksum', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('ValidateXML', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('ManualControll', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('AIPType', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('AIPpath', self.gf('django.db.models.fields.CharField')(default='/ESSArch/work', max_length=255)),
            ('PreIngestMetadata', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('IngestMetadata', self.gf('django.db.models.fields.IntegerField')(default=4)),
            ('INFORMATIONCLASS', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('IngestPath', self.gf('django.db.models.fields.CharField')(default='/ESSArch/ingest', max_length=255)),
            ('IngestDelete', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('sm_1', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('sm_type_1', self.gf('django.db.models.fields.IntegerField')(default=200)),
            ('sm_format_1', self.gf('django.db.models.fields.IntegerField')(default=103)),
            ('sm_blocksize_1', self.gf('django.db.models.fields.BigIntegerField')(default=1024)),
            ('sm_maxCapacity_1', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('sm_minChunkSize_1', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('sm_minContainerSize_1', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('sm_minCapacityWarning_1', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('sm_target_1', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('sm_2', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('sm_type_2', self.gf('django.db.models.fields.IntegerField')(default=200)),
            ('sm_format_2', self.gf('django.db.models.fields.IntegerField')(default=103)),
            ('sm_blocksize_2', self.gf('django.db.models.fields.BigIntegerField')(default=1024)),
            ('sm_maxCapacity_2', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('sm_minChunkSize_2', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('sm_minContainerSize_2', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('sm_minCapacityWarning_2', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('sm_target_2', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('sm_3', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('sm_type_3', self.gf('django.db.models.fields.IntegerField')(default=200)),
            ('sm_format_3', self.gf('django.db.models.fields.IntegerField')(default=103)),
            ('sm_blocksize_3', self.gf('django.db.models.fields.BigIntegerField')(default=1024)),
            ('sm_maxCapacity_3', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('sm_minChunkSize_3', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('sm_minContainerSize_3', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('sm_minCapacityWarning_3', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('sm_target_3', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('sm_4', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('sm_type_4', self.gf('django.db.models.fields.IntegerField')(default=200)),
            ('sm_format_4', self.gf('django.db.models.fields.IntegerField')(default=103)),
            ('sm_blocksize_4', self.gf('django.db.models.fields.BigIntegerField')(default=1024)),
            ('sm_maxCapacity_4', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('sm_minChunkSize_4', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('sm_minContainerSize_4', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('sm_minCapacityWarning_4', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('sm_target_4', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('configuration', ['ESSArchPolicy'])

        # Adding model 'ESSConfig'
        db.create_table('ESSConfig', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('Name', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('Value', self.gf('django.db.models.fields.CharField')(max_length=70, blank=True)),
            ('Status', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
        ))
        db.send_create_signal('configuration', ['ESSConfig'])

        # Adding model 'ESSProc'
        db.create_table('ESSProc', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('Name', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('Path', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('LogFile', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('Time', self.gf('django.db.models.fields.CharField')(max_length=4)),
            ('Status', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('Run', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('PID', self.gf('django.db.models.fields.IntegerField')()),
            ('Pause', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('configuration', ['ESSProc'])


    def backwards(self, orm):
        # Deleting model 'LogEvent'
        db.delete_table('configuration_logevent')

        # Deleting model 'Parameter'
        db.delete_table('configuration_parameter')

        # Deleting model 'Path'
        db.delete_table('configuration_path')

        # Deleting model 'SchemaProfile'
        db.delete_table('configuration_schemaprofile')

        # Deleting model 'IPParameter'
        db.delete_table('configuration_ipparameter')

        # Deleting model 'ESSArchPolicy'
        db.delete_table('ESSArchPolicy')

        # Deleting model 'ESSConfig'
        db.delete_table('ESSConfig')

        # Deleting model 'ESSProc'
        db.delete_table('ESSProc')


    models = {
        'configuration.essarchpolicy': {
            'AIPType': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'AIPpath': ('django.db.models.fields.CharField', [], {'default': "'/ESSArch/work'", 'max_length': '255'}),
            'AISProjectID': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'AISProjectName': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'ChecksumAlgorithm': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'INFORMATIONCLASS': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'IngestDelete': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'IngestMetadata': ('django.db.models.fields.IntegerField', [], {'default': '4'}),
            'IngestPath': ('django.db.models.fields.CharField', [], {'default': "'/ESSArch/ingest'", 'max_length': '255'}),
            'ManualControll': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'Meta': {'object_name': 'ESSArchPolicy', 'db_table': "'ESSArchPolicy'"},
            'Mode': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'PolicyID': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'PolicyName': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'PolicyStat': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'PreIngestMetadata': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'ValidateChecksum': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'ValidateXML': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'WaitProjectApproval': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sm_1': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'sm_2': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'sm_3': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'sm_4': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'sm_blocksize_1': ('django.db.models.fields.BigIntegerField', [], {'default': '1024'}),
            'sm_blocksize_2': ('django.db.models.fields.BigIntegerField', [], {'default': '1024'}),
            'sm_blocksize_3': ('django.db.models.fields.BigIntegerField', [], {'default': '1024'}),
            'sm_blocksize_4': ('django.db.models.fields.BigIntegerField', [], {'default': '1024'}),
            'sm_format_1': ('django.db.models.fields.IntegerField', [], {'default': '103'}),
            'sm_format_2': ('django.db.models.fields.IntegerField', [], {'default': '103'}),
            'sm_format_3': ('django.db.models.fields.IntegerField', [], {'default': '103'}),
            'sm_format_4': ('django.db.models.fields.IntegerField', [], {'default': '103'}),
            'sm_maxCapacity_1': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sm_maxCapacity_2': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sm_maxCapacity_3': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sm_maxCapacity_4': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sm_minCapacityWarning_1': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sm_minCapacityWarning_2': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sm_minCapacityWarning_3': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sm_minCapacityWarning_4': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sm_minChunkSize_1': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sm_minChunkSize_2': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sm_minChunkSize_3': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sm_minChunkSize_4': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sm_minContainerSize_1': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sm_minContainerSize_2': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sm_minContainerSize_3': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sm_minContainerSize_4': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sm_target_1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'sm_target_2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'sm_target_3': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'sm_target_4': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'sm_type_1': ('django.db.models.fields.IntegerField', [], {'default': '200'}),
            'sm_type_2': ('django.db.models.fields.IntegerField', [], {'default': '200'}),
            'sm_type_3': ('django.db.models.fields.IntegerField', [], {'default': '200'}),
            'sm_type_4': ('django.db.models.fields.IntegerField', [], {'default': '200'})
        },
        'configuration.essconfig': {
            'Meta': {'object_name': 'ESSConfig', 'db_table': "'ESSConfig'"},
            'Name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'Status': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'Value': ('django.db.models.fields.CharField', [], {'max_length': '70', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'configuration.essproc': {
            'LogFile': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'Meta': {'object_name': 'ESSProc', 'db_table': "'ESSProc'"},
            'Name': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'PID': ('django.db.models.fields.IntegerField', [], {}),
            'Path': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'Pause': ('django.db.models.fields.IntegerField', [], {}),
            'Run': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'Status': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'Time': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'configuration.ipparameter': {
            'Meta': {'ordering': "['type']", 'object_name': 'IPParameter'},
            'accessrestrict': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'aic_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'appraisal': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'archivist_organization': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'archivist_organization_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'archivist_organization_software': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'archivist_organization_software_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'createdate': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'creator_individual': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'creator_individual_details': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'creator_organization': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'creator_organization_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'creator_software': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'creator_software_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'datasubmissionsession': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'deliveryspecification': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'deliverytype': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'editor_organization': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'editor_organization_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'enddate': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'file_checksum': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'file_checksum_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'file_createdate': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'file_format': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'file_format_size': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'file_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'file_mime_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'file_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'file_transform_key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'file_transform_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'file_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'informationclass': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'objid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'packagenumber': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'policyid': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'preservation_organization': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'preservation_organization_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'preservation_organization_software': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'preservation_organization_software_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'previousreferencecode': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'previoussubmissionagreement': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'projectname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'receipt_email': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'recordstatus': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'referencecode': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'startdate': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'submissionagreement': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'configuration.logevent': {
            'Meta': {'ordering': "['eventType']", 'object_name': 'LogEvent'},
            'eventDetail': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'eventType': ('django.db.models.fields.IntegerField', [], {'default': '0', 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'configuration.parameter': {
            'Meta': {'ordering': "['entity']", 'object_name': 'Parameter'},
            'entity': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '70'})
        },
        'configuration.path': {
            'Meta': {'ordering': "['entity']", 'object_name': 'Path'},
            'entity': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '70'})
        },
        'configuration.schemaprofile': {
            'Meta': {'ordering': "['entity']", 'object_name': 'SchemaProfile'},
            'entity': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '70'})
        }
    }

    complete_apps = ['configuration']