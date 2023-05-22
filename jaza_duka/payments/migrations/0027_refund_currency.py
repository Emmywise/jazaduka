# Generated by Django 3.1.11 on 2021-06-10 13:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0026_auto_20210610_1228'),
    ]

    operations = [
        migrations.AddField(
            model_name='refund',
            name='currency',
            field=models.CharField(choices=[('KES', 'Ksh'), ('RWF', 'Rwf')], default='KES', max_length=5),
        ),
    ]
