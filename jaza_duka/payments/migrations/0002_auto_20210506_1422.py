# Generated by Django 3.1.9 on 2021-05-06 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='amount_auth',
            field=models.DecimalField(decimal_places=3, max_digits=10),
        ),
        migrations.AlterField(
            model_name='payment',
            name='amount_requested',
            field=models.DecimalField(decimal_places=3, max_digits=10),
        ),
    ]
