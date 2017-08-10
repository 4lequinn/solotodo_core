# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-10 20:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('metamodel', '0015_auto_20160328_1727'),
        ('solotodo', '0026_auto_20170810_1431'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='name',
        ),
        migrations.RemoveField(
            model_name='product',
            name='product_type',
        ),
        migrations.AddField(
            model_name='product',
            name='instance_model',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='metamodel.InstanceModel'),
            preserve_default=False,
        ),
    ]
