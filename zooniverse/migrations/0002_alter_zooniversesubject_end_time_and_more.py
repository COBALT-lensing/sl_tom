# Generated by Django 4.2.16 on 2024-10-02 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zooniverse', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zooniversesubject',
            name='end_time',
            field=models.DateTimeField(blank=True, help_text='Latest tie in the light curve', null=True),
        ),
        migrations.AlterField(
            model_name='zooniversesubject',
            name='start_time',
            field=models.DateTimeField(blank=True, help_text='Earliest time in the light curve', null=True),
        ),
    ]
