from django.urls import path

from .views import RefreshPayment

urlpatterns = [
    path("reload-payment", RefreshPayment.as_view(), name="reload-payment"),
]
