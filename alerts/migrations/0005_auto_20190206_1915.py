# Generated by Django 2.0.3 on 2019-02-06 19:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0004_auto_20190206_1813'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='alert',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='alert',
            name='email',
        ),
    ]
