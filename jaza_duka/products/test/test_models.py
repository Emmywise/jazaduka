import pytest

from jaza_duka.products.models import ProductsList

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
def test_products_list():
    ProductsList.objects.create(
        product_id=12345,
        description="product description",
        image_url="image url/link",
        price=10.00,
        currency="KES",
    )
    assert ProductsList.objects.count() == 1
