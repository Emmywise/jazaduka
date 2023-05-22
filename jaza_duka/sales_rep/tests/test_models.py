import pytest

from jaza_duka.sales_rep.models import SalesRep

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
def test_create_sales_rep():
    SalesRep.objects.create(
        name="Jon", phone_number=254751836813, email="test@kasha.co"
    )
    assert SalesRep.objects.count() == 1
