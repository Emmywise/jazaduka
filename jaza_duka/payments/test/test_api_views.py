from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from jaza_duka.payments.models import Outlet
from jaza_duka.utils.test_helpers import BaseAPITestCase


class TestOutletCreateView(BaseAPITestCase):
    def test_create_outlet(self):
        url = reverse("outlet-list")
        payload = {
            "outlet_code": "test100",
            "outlet_name": "test-outlet",
            "status": "AP",
            "latest_outlet_latitude": 0,
            "latest_outlet_longitude": 0,
            "phone_number": 254732697149,
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        outlet = Outlet.objects.last()
        self.assertEqual("AP", outlet.status)
        self.assertEqual("test100", outlet.outlet_code)

    def test_retrive(self):
        outlet = baker.make(Outlet, outlet_code="1234", phone_number=254732697149)
        response = self.client.get(
            reverse("outlet-detail", kwargs={"outlet_code": outlet.outlet_code})
        )
        assert response.status_code == 200
        assert response.data["phone_number"] == outlet.phone_number

    def test_patch_fails(self):
        outlet = baker.make(Outlet, outlet_code="1234", phone_number=254732697143)
        response = self.client.patch(
            reverse("outlet-detail", kwargs={"outlet_code": outlet.outlet_code}),
            {"phone_number": 254732697144},
        )
        assert response.status_code == 400

    def test_patch(self):
        outlet = baker.make(Outlet, outlet_code="12345")
        response = self.client.patch(
            reverse("outlet-detail", kwargs={"outlet_code": outlet.outlet_code}),
            {"phone_number": 254732697144},
        )
        assert response.status_code == 200
        assert response.data["phone_number"] == 254732697144
        assert response.data["outlet_name"] == outlet.outlet_name
