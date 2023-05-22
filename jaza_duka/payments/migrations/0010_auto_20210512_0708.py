# Generated by Django 3.1.9 on 2021-05-12 07:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0009_auto_20210511_1328'),
    ]

    operations = [
        migrations.RenameField(
            model_name='paymentlog',
            old_name='request_response',
            new_name='batch_request_response',
        ),
        migrations.AlterField(
            model_name='payment',
            name='pre_auth_status',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='request_status',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
