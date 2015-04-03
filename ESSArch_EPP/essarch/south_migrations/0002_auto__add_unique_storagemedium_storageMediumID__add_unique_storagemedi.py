# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding unique constraint on 'storageMedium', fields ['storageMediumID']
        db.create_unique('storageMedium', ['storageMediumID'])

        # Adding unique constraint on 'storageMedium', fields ['storageMediumUUID']
        db.create_unique('storageMedium', ['storageMediumUUID'])

        # Adding field 'storage.ObjectUUID'
        db.add_column('storage', 'ObjectUUID',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['essarch.ArchiveObject'], to_field='ObjectUUID', null=True, db_column='ObjectUUID'),
                      keep_default=False)

        # Adding field 'storage.storageMediumUUID'
        db.add_column('storage', 'storageMediumUUID',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['essarch.storageMedium'], to_field='storageMediumUUID', null=True, db_column='storageMediumUUID'),
                      keep_default=False)


    def backwards(self, orm):
        # Removing unique constraint on 'storageMedium', fields ['storageMediumUUID']
        db.delete_unique('storageMedium', ['storageMediumUUID'])

        # Removing unique constraint on 'storageMedium', fields ['storageMediumID']
        db.delete_unique('storageMedium', ['storageMediumID'])

        # Deleting field 'storage.ObjectUUID'
        db.delete_column('storage', 'ObjectUUID')

        # Deleting field 'storage.storageMediumUUID'
        db.delete_column('storage', 'storageMediumUUID')


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
            'storageMediumLocation': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'storageMediumLocationStatus': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumMounts': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumStatus': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'storageMediumUUID': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36'}),
            'storageMediumUsedCapacity': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'})
        }
    }

    complete_apps = ['essarch']