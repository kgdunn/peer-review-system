# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-10 23:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0002_auto_20170311_0000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enrolled',
            name='group',
            field=models.ForeignKey(help_text='If blank/null: used internally to enrol the rest of the class list.', null=True, on_delete=django.db.models.deletion.CASCADE, to='groups.Group'),
        ),
        migrations.AlterField(
            model_name='group',
            name='capacity',
            field=models.PositiveIntegerField(default=0, help_text='How many people in this particular group instance?'),
        ),
        migrations.AlterField(
            model_name='group',
            name='description',
            field=models.TextField(blank=True, verbose_name='Detailed group description'),
        ),
        migrations.AlterField(
            model_name='group',
            name='name',
            field=models.CharField(max_length=300, verbose_name='Group name'),
        ),
        migrations.AlterField(
            model_name='group',
            name='order',
            field=models.PositiveIntegerField(default=0, help_text='For ordering purposes in the tables.'),
        ),
        migrations.AlterField(
            model_name='group_formation_process',
            name='LTI_id',
            field=models.CharField(help_text='In Brightspace LTI post: "resource_link_id"', max_length=50, verbose_name='LTI ID'),
        ),
        migrations.AlterField(
            model_name='group_formation_process',
            name='LTI_system',
            field=models.CharField(choices=[('Brightspace-v1', 'Brightspace-v1'), ('edX-v1', 'edX-v1')], max_length=50),
        ),
        migrations.AlterField(
            model_name='group_formation_process',
            name='allow_unenroll',
            field=models.BooleanField(default=True, help_text='Can learners unenroll, which implies they will also be allowed to re-enroll, until the close off date/time.'),
        ),
        migrations.AlterField(
            model_name='group_formation_process',
            name='dt_group_selection_stops',
            field=models.DateTimeField(verbose_name='When does group selection stop'),
        ),
        migrations.AlterField(
            model_name='group_formation_process',
            name='dt_groups_open_up',
            field=models.DateTimeField(verbose_name='When can learners start to register'),
        ),
        migrations.AlterField(
            model_name='group_formation_process',
            name='dt_selfenroll_starts',
            field=models.DateTimeField(help_text='Usually the same as above date/time, but can be later', verbose_name='When does self-enrolment start?'),
        ),
        migrations.AlterField(
            model_name='group_formation_process',
            name='instructions',
            field=models.TextField(help_text='May contain HTML instructions', verbose_name='Overall instructions to learners'),
        ),
        migrations.AlterField(
            model_name='group_formation_process',
            name='random_add_unenrolled_after_cutoff',
            field=models.BooleanField(default=False, help_text='Should we randomly allocate unenrolled users after the cut-off date/time ("dt_group_selection_stops")?', verbose_name='Randomly add unenrolled learners after the cutoff date/time'),
        ),
        migrations.AlterField(
            model_name='group_formation_process',
            name='show_description',
            field=models.BooleanField(default=True, help_text='Should we show the group descriptions also?'),
        ),
        migrations.AlterField(
            model_name='group_formation_process',
            name='show_fellows',
            field=models.BooleanField(default=False, help_text='Can learners see the FirstName LastName of the other people enrolled in their groups.'),
        ),
        migrations.AlterField(
            model_name='group_formation_process',
            name='title',
            field=models.CharField(max_length=300, verbose_name='Group formation name'),
        ),
    ]
