# Generated by Django 3.1 on 2021-10-20 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_auto_20211020_0845'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductsList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.IntegerField(blank=True, null=True, unique=True)),
                ('description', models.CharField(blank=True, max_length=500, null=True, verbose_name='Description')),
                ('image_url', models.CharField(blank=True, max_length=500, null=True, verbose_name='Image Url')),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('currency', models.CharField(choices=[('KES', 'Kes'), ('RWF', 'Rwf'), ('USD', 'Usd')], default='KES', max_length=5)),
            ],
        ),
        migrations.DeleteModel(
            name='Product',
        ),
    ]
