from django.contrib import admin

from jaza_duka.payments.models import Outlet

from .models import SalesRep


@admin.register(SalesRep)
class SalesRepAdmin(admin.ModelAdmin):
    list_display = ["name", "phone_number", "email", "jaza_duka_zone"]
    search_fields = ["name", "phone_number"]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def get_readonly_fields(self, request, obj=None):
        has_outlets = Outlet.objects.filter(sales_rep=obj).exists()
        if has_outlets:
            return ["jaza_duka_zone"]
        else:
            return super().get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        has_outlets = Outlet.objects.filter(sales_rep=obj).exists()
        if has_outlets:
            return False
        return True
