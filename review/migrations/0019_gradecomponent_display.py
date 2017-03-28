# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-28 15:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0018_gradecomponent_mandatory'),
    ]

    operations = [
        migrations.AddField(
            model_name='gradecomponent',
            name='display',
            field=models.BooleanField(default=True, help_text='If False, it will not be shown; useful to show the grades currently achieved, even if the peer review process is not completely over.'),
        ),
    ]