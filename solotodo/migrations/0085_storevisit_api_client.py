# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-25 14:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('solotodo', '0084_apiclient'),
    ]

    operations = [
        migrations.AddField(
            model_name='storevisit',
            name='api_client',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to='solotodo.ApiClient'),
            preserve_default=False,
        ),
    ]