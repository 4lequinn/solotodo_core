# Generated by Django 2.0 on 2018-02-12 15:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0003_auto_20180206_1535'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='budgetentry',
            options={'ordering': ['budget', 'category__budget_ordering']},
        ),
    ]