from django.urls import include, path
from rest_framework.routers import DefaultRouter

from jaza_duka.payments import views as payments_views
from jaza_duka.payments.api import views

router = DefaultRouter()
router.register(r"", views.OutletViewSet, basename="outlet")
outlet_urls = router.urls


urlpatterns = [
    path("outlet/", include(outlet_urls)),
    path(
        "pre-auth/payment",
        payments_views.PreAuthorizationPayment.as_view(),
        name="pre_auth_payments",
    ),
    path(
        "pre-auth/payment/<int:obj_id>/",
        payments_views.GetPreAuthorizationPayment.as_view(),
        name="get_pre_auth_payment",
    ),
    path(
        "pre-auth/payment/status/<int:obj_id>/",
        payments_views.PreAuthorizationPaymentStatus.as_view(),
        name="pre_auth_status",
    ),
    path("refund/payment/", payments_views.CreateRefund.as_view()),
    path("charge/", views.ChargePaymentAPI.as_view(), name="payment-charge-api"),
]
