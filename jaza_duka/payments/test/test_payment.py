import responses
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_api_key.models import APIKey

from jaza_duka.payments.models import Outlet, Payment

from .mock_requests import (
    charge_get_response,
    charge_post_response,
    pre_auth_get_response,
    pre_auth_post_response,
)

User = get_user_model()


class TestPaymentAuthorizarion(APITestCase):
    def test_user_auth_before_pre_auth_payment(self):
        response = self.client.post(reverse("pre_auth_payments"))
        self.assertEqual(response.status_code, 403)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @responses.activate
    def test_create_pre_auth_payment(self):
        _, key = APIKey.objects.create_key(name="unit-test-service")
        self.client.credentials(HTTP_AUTHORIZATION="Api-Key {}".format(key))
        admin_user = User.objects.create_superuser(username="foo", password="bar")
        OutletObj = Outlet.objects.create(outlet_code="OUTLET1", created_by=admin_user)
        Payment.objects.create(
            outlet=OutletObj,
            order_id="12345",
            amount_auth=100.01,
            currency="KES",
            cs_agent=admin_user,
        )

        url = reverse("pre_auth_payments")
        payload = {
            "outlet": OutletObj.id,
            "order_id": "12345",
            "amount_auth": "100",
            "currency": "KES",
            "auto_charge": True,
        }
        responses.add(
            responses.POST, settings.DUKA_URL, json=pre_auth_post_response, status=202
        )
        batch_id = "KASHA_45ece6cd3857edc1b104770e7139133814ae1999_AUTH"
        responses.add(
            responses.GET,
            settings.DUKA_URL + "/" + batch_id,
            json=pre_auth_get_response,
            status=200,
        )
        responses.add(
            responses.POST, settings.DUKA_URL, json=charge_post_response, status=202
        )
        charge_batch_id = "KASHA_d8cb515ea19903daa9b146d684df639f5961ea8f_CAPTURE"
        responses.add(
            responses.GET,
            settings.DUKA_URL + "/" + charge_batch_id,
            json=charge_get_response,
            status=200,
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payment = Payment.objects.last()
        self.assertEqual("APPROVED", payment.pre_auth_confirmation_status)
        self.assertEqual("APPROVED", payment.payment_status)
        self.assertTrue(payment.pre_auth_verified)
