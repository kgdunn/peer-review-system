# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-20 09:31
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0014_auto_20170218_0709'),
    ]

    operations = [
        migrations.RenameField(
            model_name='person',
            old_name='name',
            new_name='first_name',
        ),
    ]
