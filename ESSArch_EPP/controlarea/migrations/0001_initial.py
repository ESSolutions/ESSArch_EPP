# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'permission'
        db.create_table(u'controlarea_permission', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'controlarea', ['permission'])


    def backwards(self, orm):
        # Deleting model 'permission'
        db.delete_table(u'controlarea_permission')


    models = {
        u'controlarea.permission': {
            'Meta': {'object_name': 'permission'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['controlarea']