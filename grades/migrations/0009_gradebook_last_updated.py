# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-30 11:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0008_auto_20170430_1201'),
    ]

    operations = [
        migrations.AddField(
            model_name='gradebook',
            name='last_updated',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]