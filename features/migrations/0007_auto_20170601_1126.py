# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-06-01 11:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('features', '0006_auto_20170524_1258'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment',
            name='visibility_text_filter',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
    ]
