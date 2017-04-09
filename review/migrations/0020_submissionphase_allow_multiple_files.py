# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-03 17:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0019_gradecomponent_display'),
    ]

    operations = [
        migrations.AddField(
            model_name='submissionphase',
            name='allow_multiple_files',
            field=models.BooleanField(default=False, help_text='If True, and ONLY for image files: will combine them.'),
        ),
    ]