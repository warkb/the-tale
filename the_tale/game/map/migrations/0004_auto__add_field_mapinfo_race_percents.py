# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'MapInfo.race_percents'
        db.add_column('map_mapinfo', 'race_percents',
                      self.gf('django.db.models.fields.TextField')(default='{}'),
                      keep_default=False)

    def backwards(self, orm):
        # Deleting field 'MapInfo.race_percents'
        db.delete_column('map_mapinfo', 'race_percents')

    models = {
        'map.mapinfo': {
            'Meta': {'object_name': 'MapInfo'},
            'height': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'race_percents': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'terrain': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            'terrain_percents': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'turn_number': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'width': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['map']