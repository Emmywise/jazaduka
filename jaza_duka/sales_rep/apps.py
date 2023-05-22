from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SalesRepConfig(AppConfig):
    name = "jaza_duka.sales_rep"
    verbose_name = _("SalesRep")

    def ready(self):
        try:
            import jaza_duka.sales_rep.signals  # noqa F401
        except ImportError:
            pass
