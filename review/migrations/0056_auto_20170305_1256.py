# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-05 11:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0055_auto_20170305_1254'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ritemtemplate',
            name='comment_required',
        ),
        migrations.AddField(
            model_name='ritemtemplate',
            name='option_type',
            field=models.CharField(choices=[('Radio', 'Radio buttons (default)'), ('DropD', 'Dropdown of scores'), ('LText', 'Long text [HTML Text area]'), ('SText', 'Short text [HTML input=text]')], default='Radio', max_length=5),
        ),
    ]
