# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-26 17:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0033_auto_20170226_1714'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='student_number',
            field=models.CharField(blank=True, default='', max_length=15),
        ),
    ]