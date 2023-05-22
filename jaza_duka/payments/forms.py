from django import forms
from django.core.exceptions import ValidationError

from .models import Document, Payment, Refund


class RefreshPaymentForm(forms.Form):
    ACTIONCHOICES = (("pre-auth", "Pre-Auth"), ("charge", "Charge"))
    payment_id = forms.IntegerField(required=True)
    action = forms.ChoiceField(choices=ACTIONCHOICES, required=True)

    def clean_payment_id(self):
        payment_id = self.cleaned_data.get("payment_id")
        try:
            payment_obj = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            raise ValidationError("Payment id does not exist")
        return payment_obj


class DukaUploadFileForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["document"]
        widgets = {
            "document": forms.widgets.FileInput(
                attrs={
                    "accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"  # noqa
                }
            )
        }


class RefundForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["payment_id"].queryset = Payment.objects.filter(
            refunded=False, payment_status="APPROVED"
        ).order_by("-payment_request_date")
        self.fields[
            "payment_id"
        ].label_from_instance = (
            lambda obj: f"Payment Id = {obj.id} | Order Id -{obj.order_id}"
        )

    class Meta:
        model = Refund
        fields = ["payment_id", "refunded_amount"]


class PreAuthForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["outlet"].required = True
        self.fields["outlet"].label_from_instance = lambda obj: "%s (%s)" % (
            obj.outlet_code,
            obj.outlet_name,
        )

    class Meta:
        model = Payment
        fields = ["outlet", "order_id", "amount_auth", "currency"]


class ConfirmPreAuthForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.payment_id = kwargs.pop("payment_id")
        super().__init__(*args, **kwargs)

    class Meta:
        model = Payment
        fields = ["amount_requested"]

    def clean(self):
        if self.cleaned_data.get("amount_requested") and Payment.objects.get(
            id=self.payment_id
        ).amount_auth < self.cleaned_data.get("amount_requested"):
            raise ValidationError(
                "Requested amount can not be larger than Pre-auth amount"
            )
