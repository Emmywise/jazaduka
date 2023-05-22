from rest_framework.test import APITestCase
from rest_framework_api_key.models import APIKey


class BaseAPITestCase(APITestCase):
    """ "
    Base test case with authentication so we don't have to repeat it in every test
    """

    def setUp(self):
        _, key = APIKey.objects.create_key(name="unit-test-service")
        self.client.credentials(HTTP_AUTHORIZATION="Api-Key {}".format(key))
