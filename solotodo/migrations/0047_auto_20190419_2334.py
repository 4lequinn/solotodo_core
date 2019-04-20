# Generated by Django 2.0.3 on 2019-04-19 23:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('solotodo', '0046_auto_20190418_1629'),
    ]

    operations = [
        migrations.AddField(
            model_name='storesection',
            name='is_root',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='storesection',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='solotodo.StoreSection'),
        ),
    ]
