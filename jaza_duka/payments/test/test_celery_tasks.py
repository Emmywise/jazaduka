import responses
from celery import chain
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from jaza_duka.payments.models import Outlet, Payment, PaymentLog, Refund, RefundLog
from jaza_duka.payments.tasks import confirm_get_request, post_request

from .mock_requests import (
    charge_get_response,
    charge_post_response,
    pre_auth_get_response,
    pre_auth_post_response,
    refund_get_response,
    refund_post_response,
)

User = get_user_model()


class TestCeleryTasks(TestCase):
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @responses.activate
    def test_pre_auth(self):
        # Mock the response from the payment gateway
        responses.add(
            responses.POST, settings.DUKA_URL, json=pre_auth_post_response, status=202
        )

        BATCH_URL = (
            settings.DUKA_URL + "/KASHA_45ece6cd3857edc1b104770e7139133814ae1999_AUTH"
        )

        responses.add(responses.GET, BATCH_URL, json=pre_auth_get_response, status=200)

        # Create required objects
        outlet_obj = Outlet.objects.create(
            outlet_name="Test-Outlet-1", outlet_code="TEST-OUTLET-1"
        )
        payment_obj = Payment.objects.create(
            order_id="KE822234239",
            outlet=outlet_obj,
            amount_auth=100,
        )
        payment_obj = Payment.objects.get(order_id="KE822234239")
        chain(
            post_request.s(payment_obj.id, "AR").set(countdown=1),
            confirm_get_request.s().set(countdown=10),
        ).apply_async()

        payment_obj = Payment.objects.get(order_id="KE822234239")
        log_obj = PaymentLog.objects.filter(payment_id=payment_obj).first()

        # Assertions
        self.assertEqual(
            log_obj.pre_auth_batch_id,
            "KASHA_45ece6cd3857edc1b104770e7139133814ae1999_AUTH",
        )
        self.assertEqual(log_obj.pre_auth_response, pre_auth_post_response)
        self.assertEqual(log_obj.pre_auth_get_response, pre_auth_get_response)
        self.assertTrue(payment_obj.pre_auth_verified)
        self.assertEqual(payment_obj.pre_auth_confirmation_status, "APPROVED")
        self.assertEqual(payment_obj.pre_auth_status, "Batch Received")

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @responses.activate
    def test_charge(self):
        # Mock the response from the payment gateway
        responses.add(
            responses.POST, settings.DUKA_URL, json=charge_post_response, status=202
        )

        BATCH_URL = (
            settings.DUKA_URL
            + "/KASHA_d8cb515ea19903daa9b146d684df639f5961ea8f_CAPTURE"
        )

        responses.add(responses.GET, BATCH_URL, json=charge_get_response, status=200)

        # Create required objects
        outlet_obj = Outlet.objects.create(
            outlet_name="Test-Outlet-1", outlet_code="TEST-OUTLET-1"
        )

        payment_obj = Payment.objects.create(
            order_id="KE822239",
            outlet=outlet_obj,
            amount_auth=100,
            pre_auth_confirmation_status="APPROVED",
            amount_requested=100,
        )

        PaymentLog.objects.create(
            payment_id=payment_obj,
            pre_auth_response={"response": "batch Received"},
            pre_auth_batch_id="KASHA_d8cb515ea19903daa9b146d684df639f5961ea8f_CAPTURE",
        )
        chain(
            post_request.s(payment_obj.id, "CR").set(countdown=1),
            confirm_get_request.s().set(countdown=10),
        ).apply_async()

        payment_obj = Payment.objects.get(order_id="KE822239")
        log_obj = PaymentLog.objects.filter(payment_id=payment_obj).first()

        # Assertions
        self.assertEqual(
            log_obj.pre_auth_batch_id,
            "KASHA_d8cb515ea19903daa9b146d684df639f5961ea8f_CAPTURE",
        )
        self.assertEqual(log_obj.charge_request_response, charge_post_response)

        self.assertEqual(payment_obj.pre_auth_confirmation_status, "APPROVED")
        self.assertEqual(payment_obj.payment_status, "APPROVED")
        self.assertEqual(payment_obj.payment_request_status, "Batch Received")

        self.assertIsNotNone(payment_obj.payment_request_date)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @responses.activate
    def test_refund(self):
        # Mock the response from the payment gateway
        responses.add(
            responses.POST, settings.DUKA_URL, json=refund_post_response, status=202
        )

        BATCH_URL = (
            settings.DUKA_URL + "/KASHA_0359ab95810bab36963a5c7c44bb33ff62a30b0a_REFUND"
        )

        responses.add(responses.GET, BATCH_URL, json=refund_get_response, status=200)

        # Create required objects
        outlet_obj = Outlet.objects.create(
            outlet_name="Test-Outlet-1", outlet_code="TEST-OUTLET-1"
        )

        payment_obj = Payment.objects.create(
            order_id="KE0122",
            outlet=outlet_obj,
            amount_auth=100,
            pre_auth_confirmation_status="APPROVED",
            amount_requested=100,
            payment_status="APPROVED",
        )

        PaymentLog.objects.create(
            payment_id=payment_obj,
            pre_auth_response={"response": "batch Received"},
        )

        admin_user = User.objects.create_superuser(username="foo", password="bar")

        refund_obj = Refund.objects.create(
            payment_id=payment_obj,
            refunded_amount=100,
            cs_agent=admin_user,
        )

        chain(
            post_request.s(payment_obj.id, "RR").set(countdown=1),
            confirm_get_request.s().set(countdown=10),
        ).apply_async()

        payment_obj = Payment.objects.get(order_id="KE0122")
        refund_log_obj = RefundLog.objects.get(payment_id=payment_obj)
        refund_obj = Refund.objects.get(payment_id=payment_obj)

        # Assertions
        self.assertEqual(
            refund_log_obj.refund_batch_id,
            "KASHA_0359ab95810bab36963a5c7c44bb33ff62a30b0a_REFUND",
        )
        self.assertEqual(refund_log_obj.post_request_response, refund_post_response)
        self.assertEqual(refund_log_obj.get_request_response, refund_get_response)

        self.assertEqual(refund_obj.refund_confirm_status, "APPROVED")
        self.assertEqual(refund_obj.refund_auth_status, "Batch Received")
        self.assertTrue(payment_obj.refunded)
