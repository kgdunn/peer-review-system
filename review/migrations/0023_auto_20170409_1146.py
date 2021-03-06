# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-09 09:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0022_prphase_is_visibile_to_students'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prphase',
            name='is_visibile_to_students',
            field=models.BooleanField(default=True, help_text='Show/Hide this stage from the student view.'),
        ),
    ]
