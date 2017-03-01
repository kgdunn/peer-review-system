# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-26 17:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0033_auto_20170226_1714'),
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Enrolled',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_enrolled', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='groups.Group')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='review.Person')),
            ],
        ),
        migrations.AlterField(
            model_name='group_formation_process',
            name='dt_selfenroll_starts',
            field=models.DateTimeField(help_text='Usually the same as above date/time, but can be later', verbose_name='When does self-enrolment start?'),
        ),
        migrations.AlterField(
            model_name='group_formation_process',
            name='random_add_unenrolled_after_cutoff',
            field=models.BooleanField(default=False, help_text='Should we randomly allocate unenrolled users after the cut-off date/time ("dt_group_selection_stops")?', verbose_name='Randomly add unenrolled learners after the cutoff date/time'),
        ),
    ]