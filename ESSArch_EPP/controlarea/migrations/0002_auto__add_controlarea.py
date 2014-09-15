# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'controlarea'
        db.create_table(u'controlarea_controlarea', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'controlarea', ['controlarea'])


    def backwards(self, orm):
        # Deleting model 'controlarea'
        db.delete_table(u'controlarea_controlarea')


    models = {
        u'controlarea.controlarea': {
            'Meta': {'object_name': 'controlarea'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'controlarea.permission': {
            'Meta': {'object_name': 'permission'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['controlarea']