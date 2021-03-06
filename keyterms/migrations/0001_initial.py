# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-15 14:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('review', '0026_course_base_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookletSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('n_thumbs', models.PositiveSmallIntegerField(help_text='Maximum number of thumbs up that can be awarded')),
                ('min_submissions_before_voting', models.PositiveSmallIntegerField(help_text='Minimum number of submissions before voting can start.')),
            ],
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('link_to_modified', models.ImageField(upload_to='')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='review.Person')),
            ],
        ),
        migrations.CreateModel(
            name='KeyTermTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('keyterm_text', models.CharField(max_length=254)),
                ('deadline_for_voting', models.DateTimeField()),
                ('resource_link_page_id', models.CharField(help_text='LTI post field: "resource_link_id"', max_length=50, verbose_name='Resource Link Page ID')),
            ],
        ),
    ]
