# Generated by Django 3.1.5 on 2021-02-03 18:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('min_asset_levels', '0008_auto_20210203_1755'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset_report',
            name='snipe_model_id',
            field=models.ForeignKey(db_column='snipe_model_id', on_delete=django.db.models.deletion.CASCADE, to='min_asset_levels.asset_models', to_field='snipe_model_id'),
        ),
    ]
