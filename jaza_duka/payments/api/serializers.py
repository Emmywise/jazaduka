from rest_framework import serializers

from jaza_duka.payments.models import Outlet, Payment


class OutletSerializers(serializers.ModelSerializer):
    class Meta:
        model = Outlet
        fields = "__all__"


class PaymentConfirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["order_id", "amount_requested"]
