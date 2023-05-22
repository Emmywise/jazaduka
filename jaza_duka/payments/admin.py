import logging

from celery import chain
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, reverse
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html

from .forms import ConfirmPreAuthForm, DukaUploadFileForm, PreAuthForm, RefundForm
from .models import Outlet, Payment, PaymentLog, Refund, RefundLog
from .tasks import confirm_get_request, post_request, upload_outlets

logger = logging.getLogger(__name__)


@admin.register(Outlet)
class OutletAdmin(admin.ModelAdmin):
    list_display = [
        "outlet_name",
        "outlet_code",
        "onboard",
        "status",
        "align_code",
        "route_name",
        "created_by",
        "created_at",
        "phone_number",
    ]
    search_fields = ["outlet_name", "outlet_code"]
    readonly_fields = ["created_by"]
    search_fields = ["outlet_name", "outlet_code", "created_at"]

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        return super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [
            path("upload-duka/", self.upload_duka_view, name="upload-duka"),
            path("processing-duka/", self.processing_duka_view, name="process-duka"),
        ]
        return new_urls + urls

    def upload_duka_view(self, request):
        if request.method == "POST":
            form = DukaUploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                initial_obj = form.save(commit=False)
                initial_obj.uploaded_by = request.user
                initial_obj.save()
                upload_outlets.apply_async(
                    kwargs={
                        "file_name": initial_obj.document.name,
                        "uploader_id": request.user.id,
                    },
                    countdown=5,
                )
                return HttpResponseRedirect(reverse("admin:process-duka"))

        else:
            form = DukaUploadFileForm()

        return render(request, "admin/upload_duka.html", context={"form": form})

    def processing_duka_view(self, request):
        return render(request, "admin/process_duka.html")


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "payment_id",
        "refunded_amount",
        "refund_requested_at",
        "refund_auth_status",
        "refund_confirm_status",
        "cs_agent",
    ]
    # readonly_fields = ["created_by"]
    search_fields = ["payment_id__id"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RefundLog)
class RefundLogAdmin(admin.ModelAdmin):
    list_display = ["payment_id", "refund_batch_id"]
    readonly_fields = ["created_at"]
    search_fields = ["payment_id__id", "refund_batch_id"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order_id",
        "outlet",
        "confirm_payment",
        "payment_request_date",
        "amount_auth",
        "pre_auth_status",
        "pre_auth_confirmation_status",
        "pre_auth_request_at",
        "amount_requested",
        "payment_request_status",
        "payment_status",
        "cs_agent",
    ]
    readonly_fields = ("cs_agent",)
    search_fields = ["order_id"]
    list_filter = ("pre_auth_request_at", "outlet")
    list_per_page = 20

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def confirm_payment(self, obj):
        if (
            obj.pre_auth_confirmation_status == "APPROVED"
            and not obj.payment_request_date
        ):
            return format_html(
                "<a class=`btn custom_button` href={}>Charge Payment</a>",
                reverse("admin:pre_auth_confirmation", kwargs={"id": obj.id}),
            )

        elif obj.refunded:
            return "Refunded"
        elif obj.payment_status != "APPROVED":
            return "Payment failed"
        else:
            return "Order paid"

    confirm_payment.short_description = "Payment status"

    def save_model(self, request, obj, form, change):
        obj.cs_agent = request.user
        return super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("get-pre-auth/", self.get_pre_auth_view, name="pre_auth_view"),
            path("refund/", self.refund_view, name="refund_view"),
            path(
                "processing-request/<int:id>/<str:process>",
                self.waiting_view,
                name="waiting_page",
            ),
            path(
                "processing-status/<int:id>/<str:process>",
                self.payment_status,
                name="processing_status",
            ),
            path(
                "preview/<int:id>/<str:process>",
                self.charge_preview,
                name="charge_preview",
            ),
            path(
                "confirm-pre-auth/<str:id>/",
                self.confirm_pre_auth_view,
                name="pre_auth_confirmation",
            ),
        ]
        return my_urls + urls

    def refund_view(self, request):
        if request.method == "POST":
            form = RefundForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.cs_agent = request.user
                payment_obj = Payment.objects.get(id=obj.payment_id.id)
                obj.currency = payment_obj.currency
                refunded_amount = (
                    request.POST.get("refunded_amount")
                    if request.POST.get("refunded_amount")
                    else payment_obj.amount_requested
                )
                obj.refunded_amount = refunded_amount
                obj.save()
                messages.add_message(
                    request,
                    messages.INFO,
                    "Refund request received",
                )
                chain(
                    post_request.s(obj.payment_id.id, "RR").set(countdown=1),
                    confirm_get_request.s().set(countdown=10),
                ).apply_async()
                logger.info(f"payment-id {payment_obj.id}")
                logger.info(f"order-id {payment_obj.order_id}")
                return HttpResponseRedirect(
                    reverse(
                        "admin:charge_preview", kwargs={"id": obj.id, "process": "RR"}
                    )
                )

            else:
                return render(
                    request, "admin/refund_request.html", context={"form": form}
                )

        form = RefundForm()
        return TemplateResponse(request, "admin/refund_request.html", {"form": form})

    def payment_status(self, request, id, process):
        obj = Payment.objects.get(id=int(id))
        if process == "AR" and obj.pre_auth_verified:
            return JsonResponse({"flag": True})
        elif process == "CR" and obj.payment_request_date:
            return JsonResponse({"flag": True})
        elif (
            process == "RR"
            and Refund.objects.filter(payment_id__pk=id).first().refund_confirm_status
            is not None
        ):
            return JsonResponse({"flag": True})
        return JsonResponse({"flag": False})

    def waiting_view(self, request, id, process):
        obj = Payment.objects.get(id=int(id))
        if request.method == "POST":
            if process == "AR":
                if obj.pre_auth_confirmation_status == "APPROVED":
                    messages.add_message(request, messages.INFO, "Auth was Successful")
                else:
                    try:
                        reason = PaymentLog.objects.get(
                            payment_id=obj
                        ).pre_auth_get_response["content"]["orders"][0]["reason"]
                    except Exception:
                        reason = 'Please look at "Payment Log" section'
                    messages.add_message(
                        request, messages.ERROR, "Auth Failed -{}".format(reason)
                    )
            elif process == "CR":
                if obj.payment_status == "APPROVED":
                    messages.add_message(
                        request, messages.INFO, "Payment was Successful"
                    )
                else:
                    try:
                        reason = PaymentLog.objects.get(
                            payment_id=obj
                        ).charge_request_get_response["content"]["orders"][0]["reason"]
                    except Exception:
                        reason = 'Please look at "Payment Log" section'
                    messages.add_message(
                        request, messages.ERROR, "Payment Failed - {}".format(reason)
                    )
            elif process == "RR":
                if (
                    Refund.objects.filter(payment_id__pk=id)
                    .first()
                    .refund_confirm_status
                    == "APPROVED"
                ):
                    messages.add_message(
                        request, messages.INFO, "Refund was Successful"
                    )
                else:
                    messages.add_message(request, messages.ERROR, "Refund Failed")
            return HttpResponseRedirect(reverse("admin:payments_payment_changelist"))
        return TemplateResponse(
            request, "pages/wait_page.html", {"id": obj.id, "process": process}
        )

    def charge_preview(self, request, id, process):
        if process == "CR":
            obj = Payment.objects.get(id=id)
            data_dict = {
                "currency": obj.currency,
                "amount": obj.amount_requested,
                "process": "charge",
                "order_id": obj.order_id,
            }
            if request.method == "POST":
                messages.add_message(request, messages.INFO, "Charge request received")
                return HttpResponseRedirect(
                    reverse(
                        "admin:waiting_page", kwargs={"id": obj.id, "process": "CR"}
                    )
                )

        elif process == "RR":
            obj = Refund.objects.get(id=id)
            data_dict = {
                "currency": obj.currency,
                "amount": obj.refunded_amount,
                "process": "refund",
                "order_id": obj.payment_id.order_id,
            }
            if request.method == "POST":
                messages.add_message(request, messages.INFO, "Refund request received")
                return HttpResponseRedirect(
                    reverse(
                        "admin:waiting_page",
                        kwargs={"id": obj.payment_id.id, "process": "RR"},
                    )
                )

        return TemplateResponse(request, "admin/preview.html", {"context": data_dict})

    def get_pre_auth_view(self, request):
        logger.info("start-pre-authorization")
        if request.method == "POST":
            form = PreAuthForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.cs_agent = request.user
                obj.save()
                messages.add_message(
                    request,
                    messages.INFO,
                    "Pre auth request received",
                )
                chain(
                    post_request.s(obj.id, "AR").set(countdown=1),
                    confirm_get_request.s().set(countdown=10),
                ).apply_async()
                return HttpResponseRedirect(
                    reverse(
                        "admin:waiting_page", kwargs={"id": obj.id, "process": "AR"}
                    )
                )
            else:
                return render(
                    request, "admin/get_pre_auth.html", context={"form": form}
                )

        form = PreAuthForm()
        logger.info("end-pre-authorization")
        return TemplateResponse(request, "admin/get_pre_auth.html", {"form": form})

    def confirm_pre_auth_view(self, request, id):
        logger.info("start-confirm-pre-authorization")
        try:
            payment_obj = Payment.objects.get(id=id)
            if payment_obj.pre_auth_verified:
                if request.method == "POST":
                    form = ConfirmPreAuthForm(request.POST, payment_id=id)
                    if form.is_valid():
                        request_amount = (
                            request.POST.get("amount_requested")
                            if request.POST.get("amount_requested")
                            else payment_obj.amount_auth
                        )
                        payment_obj.amount_requested = request_amount
                        payment_obj.save()
                        chain(
                            post_request.s(payment_obj.id, "CR").set(countdown=1),
                            confirm_get_request.s().set(countdown=10),
                        ).apply_async()
                        logger.info(f"payment-id {payment_obj.id}")
                        logger.info(f"order-id {payment_obj.order_id}")
                        return HttpResponseRedirect(
                            reverse(
                                "admin:charge_preview",
                                kwargs={"id": payment_obj.id, "process": "CR"},
                            )
                        )
                    else:
                        return render(
                            request,
                            "admin/confirm_pre_auth.html",
                            {"form": form, "payment_context": payment_obj},
                        )

                else:
                    form = ConfirmPreAuthForm(payment_id=id)
                    return TemplateResponse(
                        request,
                        "admin/confirm_pre_auth.html",
                        {"form": form, "payment_context": payment_obj},
                    )
            else:
                raise PermissionDenied()
        except Payment.DoesNotExist:
            messages.add_message(
                request,
                messages.INFO,
                "The resource you tried to access does\
                                      not exists",
            )
            return HttpResponseRedirect(reverse("admin:index"))


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ["payment_id", "pre_auth_batch_id"]
    search_fields = ("payment_id__order_id", "pre_auth_batch_id")
    list_filter = ("created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
