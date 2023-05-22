from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_api_key.models import APIKey

from jaza_duka.products.models import ProductsList

User = get_user_model()


class ProductApiTest(APITestCase):
    def setUp(self):
        ProductsList.objects.create(
            product_id=1235,
            description="product description",
            price=10.00,
            image_url="image/url",
            currency="KES",
        )
        _, key = APIKey.objects.create_key(name="unit-test-service")
        self.client.credentials(HTTP_AUTHORIZATION="Api-Key {}".format(key))

    def test_product_success(self):
        url = reverse("product-list")
        payload = {
            "product_id": 1231,
            "description": "one malt",
            "price": "100.00",
            "image_url": "image/link",
            "currency": "KES",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_repeated_products_id_failed(self):
        url = reverse("product-list")
        payload = {
            "product_id": 1235,
            "description": "one malt",
            "price": "100.00",
            "image_url": "image/link",
            "currency": "KES",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
