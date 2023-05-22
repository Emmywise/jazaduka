import logging

from celery import chain
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import render
from django.views import View
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from jaza_duka.payments.utils import has_identical_record

from .forms import PreAuthForm, RefreshPaymentForm, RefundForm
from .models import Payment
from .tasks import (
    confirm_get_request,
    post_request,
    sync_payment_records,
    update_wc_status,
)

logger = logging.getLogger(__name__)


class PreAuthorizationPayment(APIView):
    def post(self, request):
        logger.info("start-pre-authorization-payment")
        form = PreAuthForm(request.data)
        auto_verify = bool(request.data.get("auto_verify", None))
        auto_charge = bool(request.data.get("auto_charge", None))
        request_amount = request.data.get("amount_auth")
        logger.info(f"check-auto-charge-status {auto_charge}")
        logger.info(f"check-auto-verify-status {auto_verify}")
        if form.is_valid():
            payment_obj = form.save(commit=False)
            if request.user.is_authenticated:
                payment_obj.cs_agent = request.user
            payment_obj.amount_requested = request_amount
            payment_obj.save()
            logger.info(f"payment-id {payment_obj.id}")
            logger.info(f"order-id {payment_obj.order_id}")
            task = [
                post_request.si(payment_obj.id, "AR").set(countdown=1),
                confirm_get_request.s().set(countdown=10),
            ]
            if auto_charge:
                charge = (
                    post_request.si(payment_obj.id, "CR").set(countdown=1),
                    confirm_get_request.s().set(countdown=10),
                )
                task += charge
                if auto_verify:

                    task.append(update_wc_status.si(payment_obj.id))
            chain(*task).apply_async()
            return Response({"PROCESSING": form.data}, status=status.HTTP_201_CREATED)

        logger.info("end-pre-authorization-payment")
        return Response({"error": form.errors}, status=status.HTTP_400_BAD_REQUEST)


class PreAuthorizationPaymentStatus(APIView):
    def get(self, request, obj_id):
        try:
            payment_obj = Payment.objects.get(pk=obj_id)
            if payment_obj.payment_status == "APPROVED":
                return Response(
                    {"MESSAGE": "SUCCESSFULLY CHARGED"}, status=status.HTTP_200_OK
                )
            if payment_obj.pre_auth_confirmation_status == "APPROVED":
                return Response(
                    {"MESSAGE": "PRE AUTH APPROVED BUT NOT CHARGED"},
                    status=status.HTTP_200_OK,
                )
            if payment_obj.pre_auth_confirmation_status == "REJECTED":
                return Response({"MESSAGE": "REJECTED"}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"MESSAGE": "FAILED"}, status=status.HTTP_400_BAD_REQUEST
                )
        except Payment.DoesNotExist:
            return Response(
                {"MESSAGE": "DOES NOT EXIST"}, status=status.HTTP_404_NOT_FOUND
            )


class GetPreAuthorizationPayment(APIView):
    def get(self, request, obj_id):
        try:
            payment_obj = Payment.objects.get(pk=obj_id)
            return Response(
                {
                    "id": payment_obj.id,
                    "order ": payment_obj.order_id,
                    "outlet": payment_obj.outlet.outlet_code,
                    "amount_authorized": payment_obj.amount_auth,
                    "pre_authorization_status": payment_obj.pre_auth_status,
                    "payments_requests_date": payment_obj.payment_request_date,
                    "pre_auth_status": payment_obj.pre_auth_status,
                    "pre_auth_confirmation_status": payment_obj.pre_auth_confirmation_status,
                    "pre_auth_request_time": payment_obj.pre_auth_request_at,
                    "amounts_requested": payment_obj.amount_requested,
                    "payment_request_status": payment_obj.payment_request_status,
                    "payment_status": payment_obj.payment_status,
                    "cs_agent": payment_obj.cs_agent.username,
                }
            )
        except Payment.DoesNotExist:
            return Response({"message": "Not Found"}, status=status.HTTP_404_NOT_FOUND)


class CreateRefund(APIView):
    def post(self, request):
        form = RefundForm(request.data)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.cs_agent = request.user
            payment_obj = Payment.objects.get(id=obj.payment_id.id)
            obj.currency = payment_obj.currency
            refunded_amount = (
                request.data.get("refunded_amount")
                if request.data.get("refunded_amount")
                else payment_obj.amount_requested
            )
            obj.refunded_amount = refunded_amount
            obj.save()
            chain(
                post_request.s(obj.payment_id.id, "RR").set(countdown=1),
                confirm_get_request.s().set(countdown=10),
            ).apply_async()
            return Response(
                {"message": "PAYMENT SUCCESSFULLY REFUNDED"}, status=status.HTTP_200_OK
            )
        return Response({"error": form.errors}, status=status.HTTP_400_BAD_REQUEST)


class RefreshPayment(UserPassesTestMixin, View):
    form_class = RefreshPaymentForm
    template_name = "pages/refresh_payment.html"

    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            payment_obj = form.cleaned_data["payment_id"]
            action = form.cleaned_data["action"]
            if not has_identical_record(payment_obj, action):
                sync_payment_records.delay(payment_obj.id, action)
                message = "Changes were detected, updating database"
            else:
                message = "No changes detected for the record"
            return render(
                request,
                self.template_name,
                {"form": form, "message": message},
            )
        return render(request, self.template_name, {"form": form})
