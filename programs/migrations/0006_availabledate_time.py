# Generated by Django 4.2.10 on 2025-05-11 23:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0005_auto_20250508_0007'),
    ]

    operations = [
        migrations.AddField(
            model_name='availabledate',
            name='time',
            field=models.TimeField(default='12:00'),
        ),
    ]
