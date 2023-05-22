from rest_framework import serializers

from .models import ProductsList


class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductsList
        fields = ["product_id", "description", "price", "currency"]
