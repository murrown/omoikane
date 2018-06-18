# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-17 05:29
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('quiz', '0005_auto_20180617_0424'),
    ]

    operations = [
        migrations.AlterField(
            model_name='association',
            name='entry_id',
            field=models.IntegerField(db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='association',
            name='pos',
            field=models.CharField(max_length=100, null=True),
        ),
    ]