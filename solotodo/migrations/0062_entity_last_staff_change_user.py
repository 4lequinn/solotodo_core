# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-04 15:41
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('solotodo', '0061_entity_last_staff_change'),
    ]

    operations = [
        migrations.AddField(
            model_name='entity',
            name='last_staff_change_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
    ]
