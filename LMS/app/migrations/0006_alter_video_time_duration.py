# Generated by Django 4.1.7 on 2023-05-07 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_lesson_video'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='time_duration',
            field=models.IntegerField(null=True),
        ),
    ]
