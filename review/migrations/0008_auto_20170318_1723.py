# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-18 16:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0007_auto_20170315_1037'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gradecomponent',
            name='explanation',
            field=models.TextField(help_text='HTML is possible; used in the template. Can include template elements: {{self.grade_text}}, {{pr.___}}, {{self.n_peers}}, etc', max_length=500),
        ),
        migrations.AlterField(
            model_name='ritemtemplate',
            name='option_type',
            field=models.CharField(choices=[('Radio', 'Radio buttons (default)'), ('DropD', 'Dropdown of scores'), ('Chcks', 'Checkbox options: multiple valid answers'), ('LText', 'Long text [HTML Text area]'), ('SText', 'Short text [HTML input=text]')], default='Radio', max_length=5),
        ),
    ]