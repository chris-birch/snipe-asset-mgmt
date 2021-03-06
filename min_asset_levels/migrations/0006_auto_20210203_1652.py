# Generated by Django 3.1.5 on 2021-02-03 16:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('min_asset_levels', '0005_asset_report_model_asset_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset_models',
            name='snipe_model_id',
            field=models.IntegerField(unique=True),
        ),
        migrations.AlterField(
            model_name='asset_report',
            name='snipe_model_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='min_asset_levels.asset_models', to_field='snipe_model_id'),
        ),
    ]
