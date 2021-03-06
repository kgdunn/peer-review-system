# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-17 11:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0026_course_base_url'),
        ('keyterms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='KeyTerm_Definition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_raw', models.ImageField(blank=True, null=True, upload_to='')),
                ('image_modified', models.ImageField(blank=True, null=True, upload_to='')),
                ('image_thumbnail', models.ImageField(blank=True, null=True, upload_to='')),
                ('last_edited', models.DateTimeField(auto_now=True)),
                ('explainer_text', models.TextField()),
                ('reference_text', models.CharField(max_length=250)),
                ('allow_to_share', models.BooleanField(help_text='Student is OK to share their work with class.')),
                ('is_finalized', models.BooleanField(help_text='User has submitted, and it is after the deadline')),
            ],
        ),
        migrations.CreateModel(
            name='Thumbs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('keyterm_definition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='keyterms.KeyTerm_Definition')),
                ('voter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='review.Person')),
            ],
        ),
        migrations.RenameModel(
            old_name='KeyTermTask',
            new_name='KeyTerm_Task',
        ),
        migrations.RemoveField(
            model_name='image',
            name='person',
        ),
        migrations.DeleteModel(
            name='Image',
        ),
        migrations.AddField(
            model_name='keyterm_definition',
            name='keyterm_required',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='keyterms.KeyTerm_Task'),
        ),
        migrations.AddField(
            model_name='keyterm_definition',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='review.Person'),
        ),
    ]
