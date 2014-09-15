# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'reports'
        db.create_table(u'reports_reports', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'reports', ['reports'])


    def backwards(self, orm):
        # Deleting model 'reports'
        db.delete_table(u'reports_reports')


    models = {
        u'reports.reports': {
            'Meta': {'object_name': 'reports'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['reports']