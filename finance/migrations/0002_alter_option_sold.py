# Generated by Django 3.2.4 on 2022-07-13 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='option',
            name='sold',
            field=models.PositiveSmallIntegerField(null=True),
        ),
    ]
