# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-22 21:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0025_rubricactual_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='pr_process',
            name='dt_submissions_open_up',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='When can learners start to submit their work by'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='pr_process',
            name='dt_submission_deadline',
            field=models.DateTimeField(verbose_name='When should learners submit their work before'),
        ),
    ]