# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-12 11:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pr_process',
            options={'verbose_name': 'Peer review process', 'verbose_name_plural': 'PR processes'},
        ),
        migrations.RenameField(
            model_name='pr_process',
            old_name='all_submissions_visible_after_review',
            new_name='make_submissions_visible_after_review',
        ),
        migrations.AlterField(
            model_name='course',
            name='label',
            field=models.CharField(help_text='Obtain this from the HTML POST field: is_course_offering_sourcedid', max_length=300, verbose_name='LTI POST label'),
        ),
        migrations.AlterField(
            model_name='course',
            name='slug',
            field=models.SlugField(default='', editable=False),
        ),
        migrations.AlterField(
            model_name='pr_process',
            name='peer_reviews_start_by',
            field=models.DateTimeField(verbose_name='When does the reviewing step open for learners to start?'),
        ),
        migrations.AlterField(
            model_name='pr_process',
            name='slug',
            field=models.SlugField(default='', editable=False),
        ),
        migrations.AlterField(
            model_name='pr_process',
            name='title',
            field=models.CharField(max_length=300, verbose_name='Peer review title'),
        ),
    ]
