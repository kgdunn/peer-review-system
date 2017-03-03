# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-03 18:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0039_submission_group_submitted'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='accepted_file_types_comma_separated',
            field=models.CharField(default='PDF', help_text='Comma separated list, for example: pdf, docx, doc', max_length=100),
        ),
        migrations.AddField(
            model_name='submission',
            name='end_dt',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Learners must submit their work before'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='submission',
            name='instructions',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='submission',
            name='max_file_upload_size_MB',
            field=models.PositiveSmallIntegerField(default=10),
        ),
        migrations.AddField(
            model_name='submission',
            name='order',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='submission',
            name='start_dt',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Learners can start to submit'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='submission',
            name='templatetext',
            field=models.TextField(blank=True, default='', help_text='The template rendered to the user'),
        ),
    ]