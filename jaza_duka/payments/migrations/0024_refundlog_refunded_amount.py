# Generated by Django 3.1.11 on 2021-06-10 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0023_payment_refunded'),
    ]

    operations = [
        migrations.AddField(
            model_name='refundlog',
            name='refunded_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
