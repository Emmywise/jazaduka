import responses
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from model_bakery import baker

from jaza_duka.payments.models import Outlet, Payment, PaymentLog
from jaza_duka.users.models import User

from .mock_requests import charge_get_response, pre_auth_get_response


class RefreshPaymentTestCase(TestCase):
    def setUp(self) -> None:
        outlet = baker.make(Outlet, outlet_code="1234", phone_number=254732697143)
        payment = baker.make(
            Payment,
            outlet=outlet,
            id=1,
            order_id="12345",
            amount_auth=100.01,
            currency="KES",
        )
        baker.make(
            PaymentLog,
            payment_id=payment,
            pre_auth_batch_id="KASHA_45ece6cd3857edc1b104770e7139133814ae1999_AUTH",
            charge_request_batch_id="KASHA_d8cb515ea19903daa9b146d684df639f5961ea8f_CAPTURE",
        )
        self.url = reverse("reload-payment")
        self.client = Client()

    def test_view_authorization(self):
        response = self.client.get(self.url)
        # 302 is redirect to login page
        self.assertEqual(response.status_code, 302)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @responses.activate
    def test_sync_db(self):
        BATCH_URL = (
            settings.DUKA_URL + "/KASHA_45ece6cd3857edc1b104770e7139133814ae1999_AUTH"
        )
        responses.add(responses.GET, BATCH_URL, json=pre_auth_get_response, status=200)
        password = User.objects.make_random_password()
        self.user = User.objects.create_superuser(
            username="foobar", email="foo@bar.com", password=password
        )

        self.client.force_login(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Test reload pre-auth
        response = self.client.post(
            self.url, data={"payment_id": "1", "action": "pre-auth"}
        )
        self.assertEqual(response.status_code, 200)
        payment_obj = Payment.objects.get(id=1)
        log_obj = PaymentLog.objects.get(payment_id=payment_obj)
        self.assertEqual(log_obj.pre_auth_get_response, pre_auth_get_response)
        self.assertEqual(payment_obj.pre_auth_confirmation_status, "APPROVED")

        # Test reload charge
        BATCH_URL = (
            settings.DUKA_URL
            + "/KASHA_d8cb515ea19903daa9b146d684df639f5961ea8f_CAPTURE"
        )
        responses.add(responses.GET, BATCH_URL, json=charge_get_response, status=200)
        response = self.client.post(
            self.url, data={"payment_id": "1", "action": "charge"}
        )
        self.assertEqual(response.status_code, 200)
        payment_obj = Payment.objects.get(id=1)
        log_obj = PaymentLog.objects.get(payment_id=payment_obj)
        self.assertEqual(log_obj.charge_request_get_response, charge_get_response)
        self.assertEqual(payment_obj.payment_status, "APPROVED")
