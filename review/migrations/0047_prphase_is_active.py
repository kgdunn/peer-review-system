# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-03 21:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0046_auto_20170303_2119'),
    ]

    operations = [
        migrations.AddField(
            model_name='prphase',
            name='is_active',
            field=models.BooleanField(default=True, help_text='An override, allowing you to stage/draft phases.'),
        ),
    ]
