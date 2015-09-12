# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='controlarea',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'permissions': (('list_controlarea', 'Can list controlarea'),),
            },
        ),
        migrations.CreateModel(
            name='permission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'permissions': (('CheckinFromReception', 'CheckinFromReception'), ('CheckoutToWork', 'CheckoutToWork'), ('CheckinFromWork', 'CheckinFromWork'), ('CheckoutToGate', 'CheckoutToGate'), ('CheckinFromGate', 'CheckinFromGate'), ('DiffCheck', 'DiffCheck'), ('PreserveIP', 'PreserveIP')),
            },
        ),
    ]
