# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-17 14:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0012_auto_20170217_1455'),
    ]

    operations = [
        migrations.CreateModel(
            name='PR_process',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('LTI_system', models.CharField(choices=[('Brightspace-v1', 'Brightspace-v1'), ('edX-v1', 'edX-v1')], max_length=50)),
                ('title', models.CharField(max_length=300, verbose_name='Your peer review title')),
                ('LTI_title', models.CharField(help_text='In Brightspace LTI post: "resource_link_title"', max_length=300, verbose_name='LTI title')),
                ('slug', models.SlugField(default='', editable=False)),
                ('uses_groups', models.BooleanField(default=False, help_text='The workflow and responses are slightly modified if groups are used.')),
                ('instructions', models.TextField(help_text='May contain HTML instructions', verbose_name='Overall instructions to learners')),
                ('submission_deadline', models.DateTimeField(verbose_name='When should learners submit their work by')),
                ('peer_reviews_start_by', models.DateTimeField(verbose_name='When does the reviewing step open for learners to start?')),
                ('peer_reviews_completed_by', models.DateTimeField(verbose_name='When must learners submit their reviews by?')),
                ('peer_reviews_received_back', models.DateTimeField(verbose_name='When will learners receive their reviews back?')),
                ('show_rubric_prior_to_submission', models.BooleanField(default=False, help_text='Can learners see the rubric before they submit?')),
                ('make_submissions_visible_after_review', models.BooleanField(default=False, help_text='Can learners see all submissions from peers after the reviewing step?')),
                ('max_file_upload_size_MB', models.PositiveSmallIntegerField(default=10)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='review.Course')),
                ('rubric', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='review.RubricTemplate')),
            ],
            options={
                'verbose_name_plural': 'PR processes',
                'verbose_name': 'Peer review process',
            },
        ),
        migrations.AddField(
            model_name='submission',
            name='pr_process',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='review.PR_process', verbose_name='Peer review'),
            preserve_default=False,
        ),
    ]