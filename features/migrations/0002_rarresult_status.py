# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-09 15:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('features', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='rarresult',
            name='status',
            field=models.CharField(choices=[('empty', 'Empty'), ('done', 'Done')], default='empty', max_length=10),
        ),
    ]
