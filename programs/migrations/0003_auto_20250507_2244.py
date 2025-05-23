# Generated by Django 3.2.25 on 2025-05-07 21:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0002_review'),
    ]

    operations = [
        migrations.AddField(
            model_name='instructor',
            name='email',
            field=models.EmailField(default='email@example.com', max_length=254),
        ),
        migrations.AddField(
            model_name='instructor',
            name='phone',
            field=models.CharField(default='123-456-7890', max_length=15),
        ),
        migrations.AddField(
            model_name='instructor',
            name='rating',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=3),
        ),
        migrations.AlterField(
            model_name='instructor',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.CreateModel(
            name='Class',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('date', models.DateField()),
                ('time', models.TimeField()),
                ('instructor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_instructors', to='programs.instructor')),
            ],
        ),
        migrations.AddField(
            model_name='instructor',
            name='classes',
            field=models.ManyToManyField(related_name='instructors', to='programs.Class'),
        ),
    ]
