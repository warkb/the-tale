# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-04-20 17:48
from __future__ import unicode_literals

from django.db import migrations
import rels.django


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_remove_account_new_messages_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='gender',
            field=rels.django.RelationIntegerField(default=0),
            preserve_default=False,
        ),
    ]