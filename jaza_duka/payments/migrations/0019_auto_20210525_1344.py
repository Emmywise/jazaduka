# Generated by Django 3.1.11 on 2021-05-25 13:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0018_auto_20210525_0936'),
    ]

    operations = [
        migrations.AddField(
            model_name='outlet',
            name='outlet_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='charge_request_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
