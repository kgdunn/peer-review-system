# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-03 19:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0042_auto_20170303_2029'),
    ]

    operations = [
        migrations.CreateModel(
            name='PRPhase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(default=1)),
                ('start_dt', models.DateTimeField(verbose_name='Learners can start to submit')),
                ('end_dt', models.DateTimeField(verbose_name='Learners must submit their work before')),
                ('instructions', models.TextField(blank=True, default='')),
                ('templatetext', models.TextField(blank=True, default='', help_text='The template rendered to the user')),
                ('pr', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='review.PR_process', verbose_name='Peer review')),
            ],
        ),
        migrations.RemoveField(
            model_name='submissionphase',
            name='end_dt',
        ),
        migrations.RemoveField(
            model_name='submissionphase',
            name='id',
        ),
        migrations.RemoveField(
            model_name='submissionphase',
            name='instructions',
        ),
        migrations.RemoveField(
            model_name='submissionphase',
            name='order',
        ),
        migrations.RemoveField(
            model_name='submissionphase',
            name='pr',
        ),
        migrations.RemoveField(
            model_name='submissionphase',
            name='start_dt',
        ),
        migrations.RemoveField(
            model_name='submissionphase',
            name='templatetext',
        ),
        migrations.AddField(
            model_name='submissionphase',
            name='prphase_ptr',
            field=models.OneToOneField(auto_created=True, default=None, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='review.PRPhase'),
            preserve_default=False,
        ),
    ]
