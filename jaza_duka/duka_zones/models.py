from django.db import models
from django.utils.translation import gettext_lazy as _


class Zone(models.Model):
    name = models.CharField(_("Zone Name"), max_length=50)
    code = models.CharField(_("Zone Code"), max_length=50)

    class Meta:
        verbose_name = _("Zone")
        verbose_name_plural = _("Zones")

    def __str__(self):
        return self.name
