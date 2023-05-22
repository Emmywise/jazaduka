import logging

from celery import chain
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from jaza_duka.payments.models import Outlet, Payment
from jaza_duka.payments.tasks import confirm_get_request, post_request

from .serializers import OutletSerializers, PaymentConfirmSerializer

logger = logging.getLogger(__name__)


class OutletViewSet(viewsets.ModelViewSet):
    queryset = Outlet.objects.all()
    serializer_class = OutletSerializers
    lookup_field = "outlet_code"

    def partial_update(self, request, *args, **kwargs):
        logger.info("start-duka-outlet")
        obj = self.get_object()
        kwargs["partial"] = True

        if "phone_number" in request.data:
            if obj.phone_number and obj.phone_number != request.data["phone_number"]:
                return Response(
                    {"detail": "Phone number already allocated for this outlet"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        logger.info("end-duka-outlet")
        return self.update(request, *args, **kwargs)


class ChargePaymentAPI(GenericAPIView):
    serializer_class = PaymentConfirmSerializer

    def post(self, request, format=None):
        logger.info("start-charge-payment")
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            payment_obj = get_object_or_404(
                Payment, order_id=serializer.validated_data["order_id"]
            )
            if not (
                payment_obj.pre_auth_confirmation_status == "APPROVED"
                and not payment_obj.payment_request_date
            ):
                return Response(
                    {"message": "Provided order_id can not be processed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if float(serializer.validated_data["amount_requested"]) > float(
                payment_obj.amount_auth
            ):
                return Response(
                    {
                        "message": "Amount request can not be higher than authorized amount"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            payment_obj.amount_requested = serializer.validated_data["amount_requested"]
            payment_obj.save()
            chain(
                post_request.s(payment_obj.id, "CR").set(countdown=1),
                confirm_get_request.s().set(countdown=10),
            ).apply_async()
            return Response(
                {"message": "Charging initiated"}, status=status.HTTP_200_OK
            )
        logger.info("end-charge-payment")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
