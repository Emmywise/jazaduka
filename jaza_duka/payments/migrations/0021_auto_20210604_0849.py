# Generated by Django 3.1.11 on 2021-06-04 08:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0020_auto_20210603_1229'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='order_id',
            field=models.IntegerField(),
        ),
    ]
