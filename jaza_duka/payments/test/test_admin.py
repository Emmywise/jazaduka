# from unittest.mock import patch

import pytest
from django.urls import reverse

from jaza_duka.payments.models import Outlet, Payment, PaymentLog

# from jaza_duka.payments.tasks import confirm_get_request, post_request


# Fixtures for tests
@pytest.fixture
def OutletObj(admin_user):
    obj = Outlet.objects.create(outlet_code="OUTLET1", created_by=admin_user)
    return obj


@pytest.fixture
def PaymentObj(admin_user, OutletObj):
    Paymentobj = Payment.objects.create(
        outlet=OutletObj,
        cs_agent=admin_user,
        order_id=123,
        amount_auth=100.01,
        currency="KES",
    )
    PaymentLog.objects.create(
        payment_id=Paymentobj,
        pre_auth_response={"response": "batch Received"},
        batch_id="batchID123",
    )
    return Paymentobj


@pytest.mark.django_db
class TestPaymentsAdmin:
    def test_changelist(self, admin_client):
        url = reverse("admin:payments_payment_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_outlet_creation_form(self, admin_client):
        url = reverse("admin:payments_outlet_add")
        response = admin_client.get(url)
        assert response.status_code == 200

        response = admin_client.post(
            url,
            data={
                "outlet_code": "OUTLET1",
                "outlet_name": "test-OUTLET1",
                "status": "AP",
                "latest_outlet_latitude": 0,
                "latest_outlet_longitude": 0,
            },
        )
        assert response.status_code == 302
        assert Outlet.objects.filter(outlet_code="OUTLET1").exists()

    # TODO write tests for celery chain async functions

    # @pytest.mark.django_db
    # def test_pre_auth_view(self, admin_client, OutletObj):

    #     url = reverse("admin:pre_auth_view")
    #     response = admin_client.get(url)
    #     assert response.status_code == 200

    #     data = {
    #         "outlet": OutletObj.pk,
    #         "order_id": 1234,
    #         "amount_auth": 100.01,
    #         "currency": "KES",
    #     }
    #     response = admin_client.post(url, data=data)
    #     with patch("post_request.apply_async") as function1_mock:

    #         assert response.status_code == 302
    #         assert Payment.objects.get(order_id=1234)
    #         assert response["Location"] == reverse(
    #             "admin:waiting_page", kwargs={"id": Payment.objects.get(order_id=1234).id, "process": "AR"}
    #         )
    #         assert function1_mock.called

    # def test_confirm_auth_view(self, admin_client, PaymentObj):
    #     url = reverse("admin:pre_auth_confirmation", kwargs={"id": PaymentObj.pk})
    #     response = response = admin_client.get(url)
    #     assert response.status_code == 200

    #     data = {
    #         "amount_requested": 90.01,
    #     }
    #     response = admin_client.post(url, data=data)
    #     assert response.status_code == 302
    #     assert Payment.objects.get(order_id=123)
    #     assert Payment.objects.get(order_id=123).pre_auth_verified is True
