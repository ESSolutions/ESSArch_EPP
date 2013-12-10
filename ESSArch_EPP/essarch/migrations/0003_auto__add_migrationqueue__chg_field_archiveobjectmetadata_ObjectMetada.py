# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MigrationQueue'
        db.create_table('MigrationQueue', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ReqUUID', self.gf('django.db.models.fields.CharField')(max_length=36)),
            ('ReqType', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('ReqPurpose', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('ObjectIdentifierValue', self.gf('picklefield.fields.PickledObjectField')()),
            ('TargetMediumID', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('Status', self.gf('django.db.models.fields.IntegerField')(default=0, null=True, blank=True)),
            ('Path', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('CopyPath', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('task_id', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('posted', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'essarch', ['MigrationQueue'])


        # Changing field 'ArchiveObjectMetadata.ObjectMetadataBLOB'
        db.alter_column('IngestObjectMetadata', 'ObjectMetadataBLOB', self.gf('django.db.models.fields.TextField')(null=True))

        # Changing field 'IOqueue.sm_list'
        db.alter_column('IOqueue', 'sm_list', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'IOqueue.storageMediumID'
        db.alter_column('IOqueue', 'storageMediumID', self.gf('django.db.models.fields.CharField')(max_length=45, null=True))

        # Changing field 'IOqueue.ObjectPath'
        db.alter_column('IOqueue', 'ObjectPath', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'IOqueue.ObjectMessageDigest'
        db.alter_column('IOqueue', 'ObjectMessageDigest', self.gf('django.db.models.fields.CharField')(max_length=128, null=True))

        # Changing field 'IOqueue.ObjectIdentifierValue'
        db.alter_column('IOqueue', 'ObjectIdentifierValue', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'IOqueue.storageMediumLocation'
        db.alter_column('IOqueue', 'storageMediumLocation', self.gf('django.db.models.fields.CharField')(max_length=45, null=True))

        # Changing field 'IOqueue.t_prefix'
        db.alter_column('IOqueue', 't_prefix', self.gf('django.db.models.fields.CharField')(max_length=6, null=True))

        # Changing field 'IOqueue.work_uuid'
        db.alter_column('IOqueue', 'work_uuid', self.gf('django.db.models.fields.CharField')(max_length=36, null=True))

        # Changing field 'ESSReg001.s018'
        db.alter_column('ESSReg001', 's018', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s019'
        db.alter_column('ESSReg001', 's019', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s012'
        db.alter_column('ESSReg001', 's012', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s013'
        db.alter_column('ESSReg001', 's013', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s010'
        db.alter_column('ESSReg001', 's010', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s011'
        db.alter_column('ESSReg001', 's011', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s016'
        db.alter_column('ESSReg001', 's016', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s017'
        db.alter_column('ESSReg001', 's017', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s014'
        db.alter_column('ESSReg001', 's014', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s015'
        db.alter_column('ESSReg001', 's015', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s005'
        db.alter_column('ESSReg001', 's005', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s004'
        db.alter_column('ESSReg001', 's004', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s007'
        db.alter_column('ESSReg001', 's007', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s006'
        db.alter_column('ESSReg001', 's006', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s001'
        db.alter_column('ESSReg001', 's001', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s000'
        db.alter_column('ESSReg001', 's000', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s003'
        db.alter_column('ESSReg001', 's003', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s002'
        db.alter_column('ESSReg001', 's002', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s009'
        db.alter_column('ESSReg001', 's009', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'ESSReg001.s008'
        db.alter_column('ESSReg001', 's008', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'storageMedium.storageMediumLocation'
        db.alter_column('storageMedium', 'storageMediumLocation', self.gf('django.db.models.fields.CharField')(max_length=45, null=True))

        # Changing field 'ArchiveObject.PolicyId'
        db.alter_column('IngestObject', 'PolicyId', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['configuration.ESSArchPolicy'], to_field='PolicyID', db_column='PolicyId'))
        # Adding index on 'ArchiveObject', fields ['PolicyId']
        db.create_index('IngestObject', ['PolicyId'])


    def backwards(self, orm):
        # Removing index on 'ArchiveObject', fields ['PolicyId']
        db.delete_index('IngestObject', ['PolicyId'])

        # Deleting model 'MigrationQueue'
        db.delete_table('MigrationQueue')


        # Changing field 'ArchiveObjectMetadata.ObjectMetadataBLOB'
        db.alter_column('IngestObjectMetadata', 'ObjectMetadataBLOB', self.gf('django.db.models.fields.TextField')(default=''))

        # Changing field 'IOqueue.sm_list'
        db.alter_column('IOqueue', 'sm_list', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'IOqueue.storageMediumID'
        db.alter_column('IOqueue', 'storageMediumID', self.gf('django.db.models.fields.CharField')(default='', max_length=45))

        # Changing field 'IOqueue.ObjectPath'
        db.alter_column('IOqueue', 'ObjectPath', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'IOqueue.ObjectMessageDigest'
        db.alter_column('IOqueue', 'ObjectMessageDigest', self.gf('django.db.models.fields.CharField')(default='', max_length=128))

        # Changing field 'IOqueue.ObjectIdentifierValue'
        db.alter_column('IOqueue', 'ObjectIdentifierValue', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'IOqueue.storageMediumLocation'
        db.alter_column('IOqueue', 'storageMediumLocation', self.gf('django.db.models.fields.CharField')(default='', max_length=45))

        # Changing field 'IOqueue.t_prefix'
        db.alter_column('IOqueue', 't_prefix', self.gf('django.db.models.fields.CharField')(default='', max_length=6))

        # Changing field 'IOqueue.work_uuid'
        db.alter_column('IOqueue', 'work_uuid', self.gf('django.db.models.fields.CharField')(default='', max_length=36))

        # Changing field 'ESSReg001.s018'
        db.alter_column('ESSReg001', 's018', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s019'
        db.alter_column('ESSReg001', 's019', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s012'
        db.alter_column('ESSReg001', 's012', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s013'
        db.alter_column('ESSReg001', 's013', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s010'
        db.alter_column('ESSReg001', 's010', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s011'
        db.alter_column('ESSReg001', 's011', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s016'
        db.alter_column('ESSReg001', 's016', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s017'
        db.alter_column('ESSReg001', 's017', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s014'
        db.alter_column('ESSReg001', 's014', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s015'
        db.alter_column('ESSReg001', 's015', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s005'
        db.alter_column('ESSReg001', 's005', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s004'
        db.alter_column('ESSReg001', 's004', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s007'
        db.alter_column('ESSReg001', 's007', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s006'
        db.alter_column('ESSReg001', 's006', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s001'
        db.alter_column('ESSReg001', 's001', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s000'
        db.alter_column('ESSReg001', 's000', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s003'
        db.alter_column('ESSReg001', 's003', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s002'
        db.alter_column('ESSReg001', 's002', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s009'
        db.alter_column('ESSReg001', 's009', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'ESSReg001.s008'
        db.alter_column('ESSReg001', 's008', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'storageMedium.storageMediumLocation'
        db.alter_column('storageMedium', 'storageMediumLocation', self.gf('django.db.models.fields.CharField')(default='', max_length=45))

        # Changing field 'ArchiveObject.PolicyId'
        db.alter_column('IngestObject', 'PolicyId', self.gf('django.db.models.fields.IntegerField')(null=True))

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
        u'essarch.accessqueue': {
            'Meta': {'object_name': 'AccessQueue', 'db_table': "'AccessQueue'"},
            'ObjectIdentifierValue': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'Path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ReqPurpose': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ReqType': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'ReqUUID': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'Status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'posted': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'storageMediumID': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '45'})
        },
        u'essarch.agentidentifier': {
            'Meta': {'object_name': 'agentIdentifier', 'db_table': "'agentIdentifier'"},
            'agentIdentifierValue': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'agentName': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'agentType': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'essarch.archiveobject': {
            'CMetaMessageDigest': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'CMetaMessageDigestAlgorithm': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'CreateAgentIdentifierValue': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'CreateDate': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'DELIVERYTYPE': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'DataObjectNumItems': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'DataObjectSize': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'EntryAgentIdentifierValue': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'EntryDate': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'ExtDBdatetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'Generation': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'INFORMATIONCLASS': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'LastEventDate': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'LocalDBdatetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'Meta': {'object_name': 'ArchiveObject', 'db_table': "'IngestObject'"},
            'MetaObjectIdentifier': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'MetaObjectSize': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'OAISPackageType': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'ObjectActive': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'ObjectIdentifierValue': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'ObjectMessageDigest': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'ObjectMessageDigestAlgorithm': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'ObjectNumItems': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'ObjectPackageName': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ObjectPath': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ObjectSize': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'ObjectUUID': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36'}),
            'PMetaMessageDigest': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'PMetaMessageDigestAlgorithm': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'PolicyId': ('django.db.models.fields.related.ForeignKey', [], {'default': '0', 'to': u"orm['configuration.ESSArchPolicy']", 'to_field': "'PolicyID'", 'db_column': "'PolicyId'"}),
            'Status': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'StatusActivity': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'StatusProcess': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linkingAgentIdentifierValue': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'preservationLevelValue': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        u'essarch.archiveobjectdata': {
            'Meta': {'object_name': 'ArchiveObjectData', 'db_table': "'Object_data'"},
            'UUID': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['essarch.ArchiveObject']", 'to_field': "'ObjectUUID'", 'db_column': "'UUID'"}),
            'creator': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'enddate': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'startdate': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        u'essarch.archiveobjectmetadata': {
            'ExtDBdatetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'LocalDBdatetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'Meta': {'object_name': 'ArchiveObjectMetadata', 'db_table': "'IngestObjectMetadata'"},
            'ObjectIdentifierValue': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ObjectMetadataBLOB': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True'}),
            'ObjectMetadataServer': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'ObjectMetadataType': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'ObjectMetadataURL': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ObjectUUID': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['essarch.ArchiveObject']", 'to_field': "'ObjectUUID'", 'db_column': "'ObjectUUID'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linkingAgentIdentifierValue': ('django.db.models.fields.CharField', [], {'max_length': '45'})
        },
        u'essarch.archiveobjectrel': {
            'AIC_UUID': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'relaic_set'", 'to_field': "'ObjectUUID'", 'db_column': "'AIC_UUID'", 'to': u"orm['essarch.ArchiveObject']"}),
            'Meta': {'object_name': 'ArchiveObjectRel', 'db_table': "'Object_rel'"},
            'UUID': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reluuid_set'", 'to_field': "'ObjectUUID'", 'db_column': "'UUID'", 'to': u"orm['essarch.ArchiveObject']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'essarch.controlareaqueue': {
            'Meta': {'object_name': 'ControlAreaQueue', 'db_table': "'ReqControlAreaQueue'"},
            'ObjectIdentifierValue': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'ReqPurpose': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ReqType': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'ReqUUID': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'Status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'posted': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '45'})
        },
        u'essarch.essreg001': {
            'Meta': {'object_name': 'ESSReg001', 'db_table': "'ESSReg001'"},
            'ObjectUUID': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['essarch.ArchiveObject']", 'to_field': "'ObjectUUID'", 'db_column': "'ObjectUUID'"}),
            'i000': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i001': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i002': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i003': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i004': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i005': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i006': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i007': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i008': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i009': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i010': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i011': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i012': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i013': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i014': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i015': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i016': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i017': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i018': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'i019': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            's000': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's001': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's002': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's003': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's004': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's005': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's006': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's007': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's008': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's009': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's010': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's011': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's012': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's013': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's014': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's015': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's016': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's017': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's018': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            's019': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'})
        },
        u'essarch.eventidentifier': {
            'Meta': {'object_name': 'eventIdentifier', 'db_table': "'eventIdentifier'"},
            'eventApplication': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'eventDateTime': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'eventDetail': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'eventIdentifierValue': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36'}),
            'eventOutcome': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'eventOutcomeDetailNote': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'eventType': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'eventVersion': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linkingAgentIdentifierValue': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'linkingObjectIdentifierValue': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'essarch.eventtype_codes': {
            'Meta': {'object_name': 'eventType_codes', 'db_table': "'eventType_codes'"},
            'code': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'desc_en': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'desc_sv': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'externalDB': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'localDB': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        u'essarch.ingestqueue': {
            'Meta': {'object_name': 'IngestQueue', 'db_table': "'ReqIngestQueue'"},
            'ObjectIdentifierValue': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'ReqPurpose': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ReqType': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'ReqUUID': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'Status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'posted': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '45'})
        },
        u'essarch.ioqueue': {
            'Meta': {'object_name': 'IOqueue', 'db_table': "'IOqueue'"},
            'ObjectIdentifierValue': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'ObjectMessageDigest': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'ObjectPath': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'Status': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'WriteSize': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'cmd': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'cmdprio': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'contentLocationValue': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sm_list': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'storageMedium': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumBlockSize': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumFormat': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumID': ('django.db.models.fields.CharField', [], {'max_length': '45', 'null': 'True'}),
            'storageMediumLocation': ('django.db.models.fields.CharField', [], {'max_length': '45', 'null': 'True'}),
            't_prefix': ('django.db.models.fields.CharField', [], {'max_length': '6', 'null': 'True'}),
            'work_uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'null': 'True'})
        },
        u'essarch.migrationqueue': {
            'CopyPath': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'Meta': {'object_name': 'MigrationQueue', 'db_table': "'MigrationQueue'"},
            'ObjectIdentifierValue': ('picklefield.fields.PickledObjectField', [], {}),
            'Path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ReqPurpose': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ReqType': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'ReqUUID': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'Status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'TargetMediumID': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'posted': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'task_id': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '45'})
        },
        u'essarch.permission': {
            'Meta': {'object_name': 'permission'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'essarch.robot': {
            'Meta': {'object_name': 'robot', 'db_table': "'robot'"},
            'drive_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slot_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            't_id': ('django.db.models.fields.CharField', [], {'max_length': '6'})
        },
        u'essarch.robotdrives': {
            'IdleTime': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'Meta': {'object_name': 'robotdrives', 'db_table': "'robotdrives'"},
            'drive_dev': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'drive_firmware': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'drive_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'drive_lock': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'drive_serial': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'drive_type': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_mounts': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'slot_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            't_id': ('django.db.models.fields.CharField', [], {'max_length': '6'})
        },
        u'essarch.robotie': {
            'Meta': {'object_name': 'robotie', 'db_table': "'robotie'"},
            'drive_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slot_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            't_id': ('django.db.models.fields.CharField', [], {'max_length': '6'})
        },
        u'essarch.robotreq': {
            'Meta': {'object_name': 'robotreq', 'db_table': "'robotreq'"},
            'ReqPurpose': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_prio': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'req_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            't_id': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'work_uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'essarch.storage': {
            'ExtDBdatetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'LocalDBdatetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'Meta': {'object_name': 'storage', 'db_table': "'storage'"},
            'ObjectIdentifierValue': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ObjectUUID': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['essarch.ArchiveObject']", 'to_field': "'ObjectUUID'", 'null': 'True', 'db_column': "'ObjectUUID'"}),
            'contentLocation': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'contentLocationType': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'contentLocationValue': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'storageMediumID': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'storageMediumUUID': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['essarch.storageMedium']", 'to_field': "'storageMediumUUID'", 'null': 'True', 'db_column': "'storageMediumUUID'"})
        },
        u'essarch.storagemedium': {
            'CreateAgentIdentifierValue': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'CreateDate': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'ExtDBdatetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'LocalDBdatetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'Meta': {'object_name': 'storageMedium', 'db_table': "'storageMedium'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linkingAgentIdentifierValue': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'storageMedium': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumBlockSize': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumDate': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'storageMediumFormat': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumID': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '45'}),
            'storageMediumLocation': ('django.db.models.fields.CharField', [], {'max_length': '45', 'null': 'True'}),
            'storageMediumLocationStatus': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumMounts': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumStatus': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumUUID': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36'}),
            'storageMediumUsedCapacity': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'})
        }
    }

    complete_apps = ['essarch']