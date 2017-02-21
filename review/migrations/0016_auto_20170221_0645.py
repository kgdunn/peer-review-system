# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-21 06:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0015_auto_20170220_0931'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pr_process',
            name='rubric',
        ),
        migrations.RemoveField(
            model_name='rubrictemplate',
            name='id',
        ),
        migrations.AddField(
            model_name='rubrictemplate',
            name='pr_process',
            field=models.OneToOneField(default=None, on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='review.PR_process'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='submission',
            name='is_valid',
            field=models.BooleanField(default=False, help_text='Valid if: it was submitted on time, or if this is the most recent submission (there might be older ones).'),
        ),
    ]
