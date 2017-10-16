# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-03 18:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solotodo', '0094_auto_20171001_1550'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='lead',
            options={'ordering': ('entity_history', 'timestamp'), 'permissions': (('view_leads_user_data', 'Can view the IP and user associated to all leads'), ('backend_list_leads', 'Can view list of leads in the backend'))},
        ),
    ]