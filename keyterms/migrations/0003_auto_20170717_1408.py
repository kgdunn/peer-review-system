# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-17 12:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('keyterms', '0002_auto_20170717_1345'),
    ]

    operations = [
        migrations.DeleteModel(
            name='BookletSettings',
        ),
        migrations.AddField(
            model_name='keyterm_definition',
            name='definition_text',
            field=models.CharField(blank=True, help_text='Capped at 500 characters.', max_length=505, null=True),
        ),
        migrations.AddField(
            model_name='keyterm_task',
            name='max_thumbs',
            field=models.PositiveSmallIntegerField(default=3, help_text='Maximum number of thumbs up that can be awarded'),
        ),
        migrations.AddField(
            model_name='keyterm_task',
            name='min_submissions_before_voting',
            field=models.PositiveSmallIntegerField(default=10, help_text='Minimum number of submissions before voting can start.'),
        ),
        migrations.AddField(
            model_name='thumbs',
            name='awarded',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='thumbs',
            name='last_edited',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]