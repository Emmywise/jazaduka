import responses
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_api_key.models import APIKey

from jaza_duka.payments.models import Outlet, Payment, PaymentLog

from .mock_requests import charge_get_response, charge_post_response

User = get_user_model()


class ChargeApiTest(APITestCase):
    def setUp(self):
        admin_user = User.objects.create_superuser(username="foo", password="bar")
        outlet_obj = Outlet.objects.create(outlet_code="OUTLET1", created_by=admin_user)
        payment_obj = Payment.objects.create(
            outlet=outlet_obj,
            order_id="KE123",
            amount_auth=100.01,
            currency="KES",
            pre_auth_confirmation_status="APPROVED",
            cs_agent=admin_user,
        )
        PaymentLog.objects.create(
            payment_id=payment_obj,
            pre_auth_response={"response": "batch Received"},
            pre_auth_batch_id="batchID123",
        )
        _, key = APIKey.objects.create_key(name="unit-test-service")
        self.client.credentials(HTTP_AUTHORIZATION="Api-Key {}".format(key))

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @responses.activate
    def test_charge_api(self):
        url = reverse("payment-charge-api")
        payload = {
            "order_id": "KE123",
            "amount_requested": "100",
        }

        responses.add(
            responses.POST, settings.DUKA_URL, json=charge_post_response, status=202
        )

        batch_id = "KASHA_d8cb515ea19903daa9b146d684df639f5961ea8f_CAPTURE"
        responses.add(
            responses.GET,
            settings.DUKA_URL + "/" + batch_id,
            json=charge_get_response,
            status=200,
        )

        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payment = Payment.objects.last()
        self.assertEqual("APPROVED", payment.payment_status)
        self.assertIsNotNone(payment.payment_request_date)

        # Send the request again this time it should fail because payment is already processed for the order_id
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
