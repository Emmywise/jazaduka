from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_api_key.models import APIKey

from jaza_duka.payments.models import Outlet
from jaza_duka.sales_rep.models import SalesRep


class GetDukaSalesRepNumber(APITestCase):
    def setUp(self):
        SalesRep.objects.create(
            name="test", phone_number=254115253368, email="test@kasha.com"
        )
        _, key = APIKey.objects.create_key(name="unit-test-service")
        self.client.credentials(HTTP_AUTHORIZATION="Api-Key {}".format(key))

    def test_duka_salesrep_phonenumber(self):

        url = reverse("duka-sales-rep-number")
        payload = {
            "phonenumber": 254115253368,
        }
        response = self.client.get(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_activated_duka(self):
        Outlet.objects.create(
            outlet_code="test100",
            outlet_name="test",
            status="AP",
            phone_number=254115253367,
        )
        url = reverse("duka-sales-rep-number")
        payload = {
            "phonenumber": 254115253367,
        }
        response = self.client.get(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_not_activated_duka(self):
        Outlet.objects.create(
            outlet_code="test200",
            outlet_name="test",
            status="PD",
            phone_number=254115253366,
        )
        url = reverse("duka-sales-rep-number")
        payload = {
            "phonenumber": 254115253366,
        }
        response = self.client.get(url, payload)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
