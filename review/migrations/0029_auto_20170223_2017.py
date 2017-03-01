# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-23 20:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0028_auto_20170223_1926'),
    ]

    operations = [
        migrations.AlterField(
            model_name='roptiontemplate',
            name='option_type',
            field=models.CharField(choices=[('Radio', 'Radio buttons (default)'), ('LText', 'Long text [HTML Text area]'), ('SText', 'Short text [HTML input=text]')], default='Radio', max_length=5),
        ),
    ]