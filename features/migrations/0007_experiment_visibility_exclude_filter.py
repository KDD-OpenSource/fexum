# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-06-06 20:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('features', '0006_auto_20170524_1258'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='visibility_exclude_filter',
            field=models.CharField(default='', max_length=150),
        ),
    ]