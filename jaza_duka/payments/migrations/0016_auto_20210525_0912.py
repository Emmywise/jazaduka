# Generated by Django 3.1.11 on 2021-05-25 09:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0015_auto_20210525_0831'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentlog',
            name='pre_auth_response',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
