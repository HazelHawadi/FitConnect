# Generated by Django 3.2.25 on 2025-05-08 11:29

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
