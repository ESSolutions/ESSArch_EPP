# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'permission'
        db.create_table(u'essarch_permission', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'essarch', ['permission'])

        # Adding model 'ArchiveObject'
        db.create_table('IngestObject', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ObjectUUID', self.gf('django.db.models.fields.CharField')(unique=True, max_length=36)),
            ('PolicyId', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('ObjectIdentifierValue', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('ObjectPackageName', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ObjectSize', self.gf('django.db.models.fields.BigIntegerField')(null=True)),
            ('ObjectNumItems', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('ObjectMessageDigestAlgorithm', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('ObjectMessageDigest', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('ObjectPath', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ObjectActive', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('MetaObjectIdentifier', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('MetaObjectSize', self.gf('django.db.models.fields.BigIntegerField')(null=True)),
            ('CMetaMessageDigestAlgorithm', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('CMetaMessageDigest', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('PMetaMessageDigestAlgorithm', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('PMetaMessageDigest', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('DataObjectSize', self.gf('django.db.models.fields.BigIntegerField')(null=True)),
            ('DataObjectNumItems', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('Status', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('StatusActivity', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('StatusProcess', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('LastEventDate', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('linkingAgentIdentifierValue', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('CreateDate', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('CreateAgentIdentifierValue', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('EntryDate', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('EntryAgentIdentifierValue', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('OAISPackageType', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('preservationLevelValue', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('DELIVERYTYPE', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('INFORMATIONCLASS', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('Generation', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('LocalDBdatetime', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('ExtDBdatetime', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'essarch', ['ArchiveObject'])

        # Adding model 'ArchiveObjectData'
        db.create_table('Object_data', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('UUID', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['essarch.ArchiveObject'], to_field='ObjectUUID', db_column='UUID')),
            ('creator', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('startdate', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('enddate', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'essarch', ['ArchiveObjectData'])

        # Adding model 'ArchiveObjectMetadata'
        db.create_table('IngestObjectMetadata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ObjectUUID', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['essarch.ArchiveObject'], to_field='ObjectUUID', db_column='ObjectUUID')),
            ('ObjectIdentifierValue', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ObjectMetadataType', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('ObjectMetadataServer', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('ObjectMetadataURL', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ObjectMetadataBLOB', self.gf('django.db.models.fields.TextField')()),
            ('linkingAgentIdentifierValue', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('LocalDBdatetime', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('ExtDBdatetime', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'essarch', ['ArchiveObjectMetadata'])

        # Adding model 'ArchiveObjectRel'
        db.create_table('Object_rel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('AIC_UUID', self.gf('django.db.models.fields.related.ForeignKey')(related_name='relaic_set', to_field='ObjectUUID', db_column='AIC_UUID', to=orm['essarch.ArchiveObject'])),
            ('UUID', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reluuid_set', to_field='ObjectUUID', db_column='UUID', to=orm['essarch.ArchiveObject'])),
        ))
        db.send_create_signal(u'essarch', ['ArchiveObjectRel'])

        # Adding model 'agentIdentifier'
        db.create_table('agentIdentifier', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('agentIdentifierValue', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('agentName', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('agentType', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal(u'essarch', ['agentIdentifier'])

        # Adding model 'eventIdentifier'
        db.create_table('eventIdentifier', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('eventIdentifierValue', self.gf('django.db.models.fields.CharField')(unique=True, max_length=36)),
            ('eventType', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('eventDateTime', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('eventDetail', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('eventApplication', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('eventVersion', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('eventOutcome', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('eventOutcomeDetailNote', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('linkingAgentIdentifierValue', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('linkingObjectIdentifierValue', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'essarch', ['eventIdentifier'])

        # Adding model 'eventType_codes'
        db.create_table('eventType_codes', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('desc_sv', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('desc_en', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('localDB', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('externalDB', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal(u'essarch', ['eventType_codes'])

        # Adding model 'IOqueue'
        db.create_table('IOqueue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cmd', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('cmdprio', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('work_uuid', self.gf('django.db.models.fields.CharField')(max_length=36)),
            ('ObjectIdentifierValue', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ObjectMessageDigest', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('ObjectPath', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('storageMedium', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('storageMediumID', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('sm_list', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('storageMediumBlockSize', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('storageMediumFormat', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('contentLocationValue', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('storageMediumLocation', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('t_prefix', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('WriteSize', self.gf('django.db.models.fields.BigIntegerField')(null=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('Status', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal(u'essarch', ['IOqueue'])

        # Adding model 'ESSReg001'
        db.create_table('ESSReg001', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ObjectUUID', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['essarch.ArchiveObject'], to_field='ObjectUUID', db_column='ObjectUUID')),
            ('i000', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i001', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i002', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i003', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i004', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i005', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i006', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i007', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i008', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i009', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i010', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i011', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i012', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i013', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i014', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i015', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i016', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i017', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i018', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('i019', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('s000', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s001', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s002', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s003', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s004', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s005', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s006', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s007', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s008', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s009', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s010', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s011', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s012', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s013', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s014', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s015', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s016', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s017', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s018', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('s019', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'essarch', ['ESSReg001'])

        # Adding model 'ControlAreaQueue'
        db.create_table('ReqControlAreaQueue', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ReqUUID', self.gf('django.db.models.fields.CharField')(max_length=36)),
            ('ReqType', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('ReqPurpose', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('ObjectIdentifierValue', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('Status', self.gf('django.db.models.fields.IntegerField')(default=0, null=True, blank=True)),
            ('posted', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'essarch', ['ControlAreaQueue'])

        # Adding model 'AccessQueue'
        db.create_table('AccessQueue', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ReqUUID', self.gf('django.db.models.fields.CharField')(max_length=36)),
            ('ReqType', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('ReqPurpose', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('ObjectIdentifierValue', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('storageMediumID', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('Status', self.gf('django.db.models.fields.IntegerField')(default=0, null=True, blank=True)),
            ('Path', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('posted', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'essarch', ['AccessQueue'])

        # Adding model 'IngestQueue'
        db.create_table('ReqIngestQueue', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ReqUUID', self.gf('django.db.models.fields.CharField')(max_length=36)),
            ('ReqType', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('ReqPurpose', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('ObjectIdentifierValue', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('Status', self.gf('django.db.models.fields.IntegerField')(default=0, null=True, blank=True)),
            ('posted', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'essarch', ['IngestQueue'])

        # Adding model 'storageMedium'
        db.create_table('storageMedium', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('storageMediumUUID', self.gf('django.db.models.fields.CharField')(max_length=36)),
            ('storageMedium', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('storageMediumID', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('storageMediumDate', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('storageMediumLocation', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('storageMediumLocationStatus', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('storageMediumBlockSize', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('storageMediumUsedCapacity', self.gf('django.db.models.fields.BigIntegerField')(null=True)),
            ('storageMediumStatus', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('storageMediumFormat', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('storageMediumMounts', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('linkingAgentIdentifierValue', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('CreateDate', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('CreateAgentIdentifierValue', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('LocalDBdatetime', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('ExtDBdatetime', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'essarch', ['storageMedium'])

        # Adding model 'storage'
        db.create_table('storage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contentLocation', self.gf('django.db.models.fields.BigIntegerField')(null=True)),
            ('ObjectIdentifierValue', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('contentLocationType', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('contentLocationValue', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('storageMediumID', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('LocalDBdatetime', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('ExtDBdatetime', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'essarch', ['storage'])

        # Adding model 'robot'
        db.create_table('robot', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slot_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('drive_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('t_id', self.gf('django.db.models.fields.CharField')(max_length=6)),
        ))
        db.send_create_signal(u'essarch', ['robot'])

        # Adding model 'robotdrives'
        db.create_table('robotdrives', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('drive_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('t_id', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('slot_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('num_mounts', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('drive_dev', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('drive_type', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('drive_serial', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('drive_firmware', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('drive_lock', self.gf('django.db.models.fields.CharField')(max_length=36)),
            ('IdleTime', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal(u'essarch', ['robotdrives'])

        # Adding model 'robotie'
        db.create_table('robotie', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slot_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('drive_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('t_id', self.gf('django.db.models.fields.CharField')(max_length=6)),
        ))
        db.send_create_signal(u'essarch', ['robotie'])

        # Adding model 'robotreq'
        db.create_table('robotreq', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('job_prio', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('req_type', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('t_id', self.gf('django.db.models.fields.CharField')(max_length=6, blank=True)),
            ('work_uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('ReqPurpose', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'essarch', ['robotreq'])


    def backwards(self, orm):
        # Deleting model 'permission'
        db.delete_table(u'essarch_permission')

        # Deleting model 'ArchiveObject'
        db.delete_table('IngestObject')

        # Deleting model 'ArchiveObjectData'
        db.delete_table('Object_data')

        # Deleting model 'ArchiveObjectMetadata'
        db.delete_table('IngestObjectMetadata')

        # Deleting model 'ArchiveObjectRel'
        db.delete_table('Object_rel')

        # Deleting model 'agentIdentifier'
        db.delete_table('agentIdentifier')

        # Deleting model 'eventIdentifier'
        db.delete_table('eventIdentifier')

        # Deleting model 'eventType_codes'
        db.delete_table('eventType_codes')

        # Deleting model 'IOqueue'
        db.delete_table('IOqueue')

        # Deleting model 'ESSReg001'
        db.delete_table('ESSReg001')

        # Deleting model 'ControlAreaQueue'
        db.delete_table('ReqControlAreaQueue')

        # Deleting model 'AccessQueue'
        db.delete_table('AccessQueue')

        # Deleting model 'IngestQueue'
        db.delete_table('ReqIngestQueue')

        # Deleting model 'storageMedium'
        db.delete_table('storageMedium')

        # Deleting model 'storage'
        db.delete_table('storage')

        # Deleting model 'robot'
        db.delete_table('robot')

        # Deleting model 'robotdrives'
        db.delete_table('robotdrives')

        # Deleting model 'robotie'
        db.delete_table('robotie')

        # Deleting model 'robotreq'
        db.delete_table('robotreq')


    models = {
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
            'PolicyId': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
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
            'ObjectMetadataBLOB': ('django.db.models.fields.TextField', [], {}),
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
            's000': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's001': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's002': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's003': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's004': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's005': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's006': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's007': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's008': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's009': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's010': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's011': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's012': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's013': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's014': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's015': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's016': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's017': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's018': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            's019': ('django.db.models.fields.CharField', [], {'max_length': '255'})
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
            'ObjectIdentifierValue': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ObjectMessageDigest': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'ObjectPath': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'Status': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'WriteSize': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'cmd': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'cmdprio': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'contentLocationValue': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sm_list': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'storageMedium': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumBlockSize': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumFormat': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumID': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'storageMediumLocation': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            't_prefix': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'work_uuid': ('django.db.models.fields.CharField', [], {'max_length': '36'})
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
            'contentLocation': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'contentLocationType': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'contentLocationValue': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'storageMediumID': ('django.db.models.fields.CharField', [], {'max_length': '45'})
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
            'storageMediumID': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'storageMediumLocation': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'storageMediumLocationStatus': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumMounts': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumStatus': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumUUID': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'storageMediumUsedCapacity': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'})
        }
    }

    complete_apps = ['essarch']