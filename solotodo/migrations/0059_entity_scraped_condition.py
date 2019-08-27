# Generated by Django 2.0.3 on 2019-08-07 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solotodo', '0058_store_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='entity',
            name='scraped_condition',
            field=models.URLField(choices=[('https://schema.org/DamagedCondition', 'Damaged'), ('https://schema.org/NewCondition', 'New'), ('https://schema.org/RefurbishedCondition', 'Refurbished'), ('https://schema.org/UsedCondition', 'Used')], default='https://schema.org/NewCondition'),
            preserve_default=False,
        ),
    ]