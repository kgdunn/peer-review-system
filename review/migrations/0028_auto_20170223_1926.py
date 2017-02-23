# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-23 19:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0027_auto_20170223_0939'),
    ]

    operations = [
        migrations.AddField(
            model_name='roptiontemplate',
            name='option_type',
            field=models.CharField(choices=[('Radio', 'Radio buttons (default'), ('LText', 'Long text [HTML Text area]'), ('SText', 'Short text [HTML input=text]')], default='Radio', max_length=5),
        ),
        migrations.AlterField(
            model_name='pr_process',
            name='dt_peer_reviews_received_back',
            field=models.DateTimeField(verbose_name='When will learners receive their results back?'),
        ),
    ]
