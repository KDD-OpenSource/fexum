# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-04-06 13:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('features', '0003_auto_20170308_1356'),
    ]

    operations = [
        migrations.CreateModel(
            name='Spectrogram',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('width', models.IntegerField()),
                ('height', models.IntegerField()),
                ('image', models.FileField(upload_to='')),
                ('feature', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='features.Feature')),
            ],
        ),
    ]