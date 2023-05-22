import requests
from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

CURRENCY_CHOICES = (("KES", "KES"), ("RWF", "RWF"), ("USD", "USD"))


class ProductsList(models.Model):
    product_id = models.IntegerField(null=True, blank=False, unique=True)
    description = models.CharField(
        _("Description"), null=True, blank=False, max_length=500
    )
    image_url = models.CharField(_("Image Url"), null=True, blank=True, max_length=500)
    price = models.DecimalField(null=True, blank=False, max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, choices=CURRENCY_CHOICES, default="KES")

    def __str__(self):
        return "%s" % self.description


@receiver(post_delete, sender=ProductsList)
def unmark_on_delete(sender, instance, **kwargs):
    url = f"{settings.USSD_URL}sync/jazaduka/product/{instance.product_id}/"
    data = {
        "woocommerce_item_id": instance.product_id,
        "price": instance.price,
        "en": instance.description,
    }
    requests.delete(url, data=data)


@receiver(post_save, sender=ProductsList)
def update_save(sender, instance, **kwargs):
    url = f"{settings.USSD_URL}sync/jazaduka/product/{instance.product_id}/"
    data = {
        "woocommerce_item_id": instance.product_id,
        "price": instance.price,
        "en": instance.description,
    }
    requests.put(url, data=data)
