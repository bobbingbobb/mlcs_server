# Generated by Django 2.1 on 2018-12-15 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0008_auto_20181215_1458'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cimage',
            name='repo',
            field=models.CharField(max_length=50),
        ),
    ]