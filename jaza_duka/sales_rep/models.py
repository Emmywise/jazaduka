from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from jaza_duka.duka_zones.models import Zone
from jaza_duka.sales_rep.utils import clean_phone_number


class SalesRep(models.Model):
    name = models.CharField(_("Sales Rep name"), max_length=50)
    phone_number = models.BigIntegerField(unique=True)
    email = models.EmailField(_("Email"), max_length=254)
    jaza_duka_zone = models.ForeignKey(
        Zone, verbose_name=_("Zone"), on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = _("SalesRep")
        verbose_name_plural = _("SalesReps")

    def __str__(self):
        return self.name

    def clean(self):
        valid = clean_phone_number(self.phone_number)
        if not valid:
            raise ValidationError(
                {
                    "phone_number": "Phone number should be in E164 format (Kenya or Rwanda) without the + sign"
                }
            )

        if "@kasha.co" not in self.email:
            raise ValidationError({"email": "Email should be in kasha.co domain"})

    def save(self, **kwargs):
        self.full_clean()
        return super().save(**kwargs)
