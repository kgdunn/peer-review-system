# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-03 19:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0040_auto_20170303_1957'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubmissionPhase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(default=1)),
                ('start_dt', models.DateTimeField(verbose_name='Learners can start to submit')),
                ('end_dt', models.DateTimeField(verbose_name='Learners must submit their work before')),
                ('instructions', models.TextField(blank=True, default='')),
                ('templatetext', models.TextField(blank=True, default='', help_text='The template rendered to the user')),
                ('max_file_upload_size_MB', models.PositiveSmallIntegerField(default=10)),
                ('accepted_file_types_comma_separated', models.CharField(default='PDF', help_text='Comma separated list, for example: pdf, docx, doc', max_length=100)),
                ('pr_process', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='review.PR_process', verbose_name='Peer review')),
            ],
        ),
        migrations.RemoveField(
            model_name='submission',
            name='accepted_file_types_comma_separated',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='end_dt',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='instructions',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='max_file_upload_size_MB',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='order',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='start_dt',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='templatetext',
        ),
    ]
