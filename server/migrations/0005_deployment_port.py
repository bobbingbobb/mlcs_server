# Generated by Django 2.1 on 2018-10-22 03:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0004_deployment_test'),
    ]

    operations = [
        migrations.AddField(
            model_name='deployment',
            name='port',
            field=models.IntegerField(default=0),
        ),
    ]
