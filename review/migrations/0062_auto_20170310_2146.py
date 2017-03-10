# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-10 20:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0061_auto_20170310_1858'),
    ]

    operations = [
        migrations.AddField(
            model_name='rubrictemplate',
            name='id',
            field=models.AutoField(auto_created=True, default=None, primary_key=True, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='rubrictemplate',
            name='pr_process',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='review.PR_process'),
        ),
    ]
