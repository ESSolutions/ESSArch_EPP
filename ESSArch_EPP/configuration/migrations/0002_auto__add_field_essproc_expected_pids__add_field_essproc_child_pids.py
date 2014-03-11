# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ESSProc.expected_pids'
        db.add_column('ESSProc', 'expected_pids',
                      self.gf('django.db.models.fields.IntegerField')(default=1),
                      keep_default=False)

        # Adding field 'ESSProc.child_pids'
        db.add_column('ESSProc', 'child_pids',
                      self.gf('picklefield.fields.PickledObjectField')(null=True),
                      keep_default=False)

        # Adding field 'ESSProc.checked'
        db.add_column('ESSProc', 'checked',
                      self.gf('django.db.models.fields.DateTimeField')(default='2014-01-01 00:01'),
                      keep_default=False)

        # Adding field 'ESSProc.alarm'
        db.add_column('ESSProc', 'alarm',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'ESSProc.expected_pids'
        db.delete_column('ESSProc', 'expected_pids')

        # Deleting field 'ESSProc.child_pids'
        db.delete_column('ESSProc', 'child_pids')

        # Deleting field 'ESSProc.checked'
        db.delete_column('ESSProc', 'checked')

        # Deleting field 'ESSProc.alarm'
        db.delete_column('ESSProc', 'alarm')


    models = {
        u'configuration.essarchpolicy': {
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
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
        u'configuration.essconfig': {
            'Meta': {'object_name': 'ESSConfig', 'db_table': "'ESSConfig'"},
            'Name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'Status': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'Value': ('django.db.models.fields.CharField', [], {'max_length': '70', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'configuration.essproc': {
            'LogFile': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'Meta': {'object_name': 'ESSProc', 'db_table': "'ESSProc'"},
            'Name': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'PID': ('django.db.models.fields.IntegerField', [], {}),
            'Path': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'Pause': ('django.db.models.fields.IntegerField', [], {}),
            'Run': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'Status': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'Time': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'alarm': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'child_pids': ('picklefield.fields.PickledObjectField', [], {'null': 'True'}),
            'expected_pids': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'monitoring': ('django.db.models.fields.DateTimeField', [], {'default': "'2014-01-01 00:00'"})
        },
        u'configuration.ipparameter': {
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
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
        u'configuration.logevent': {
            'Meta': {'ordering': "['eventType']", 'object_name': 'LogEvent'},
            'eventDetail': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'eventType': ('django.db.models.fields.IntegerField', [], {'default': '0', 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'configuration.parameter': {
            'Meta': {'ordering': "['entity']", 'object_name': 'Parameter'},
            'entity': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '70'})
        },
        u'configuration.path': {
            'Meta': {'ordering': "['entity']", 'object_name': 'Path'},
            'entity': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '70'})
        },
        u'configuration.schemaprofile': {
            'Meta': {'ordering': "['entity']", 'object_name': 'SchemaProfile'},
            'entity': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '70'})
        }
    }

    complete_apps = ['configuration']