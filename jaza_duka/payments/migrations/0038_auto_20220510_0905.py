# Generated by Django 3.1 on 2022-05-10 09:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0037_auto_20220121_0602'),
    ]

    operations = [
        migrations.AlterField(
            model_name='outlet',
            name='align_code',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
