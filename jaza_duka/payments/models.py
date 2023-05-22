from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils.translation import gettext_lazy as _

from jaza_duka.sales_rep.models import SalesRep
from jaza_duka.sales_rep.utils import clean_phone_number

CURRENCY_CHOICES = (("KES", "Ksh"), ("RWF", "Rwf"))

DUKA_STORE_STATUS_CHOICES = (
    ("AP", "APPROVED"),
    ("PD", "PENDING"),
    ("RJ", "REJECTED"),
)


class Outlet(models.Model):
    outlet_code = models.CharField(max_length=100, unique=True)
    outlet_name = models.CharField(
        _("Duka's Outlet Name"), max_length=100, null=True, blank=True
    )
    sales_rep = models.ForeignKey(
        SalesRep,
        verbose_name=_("Sales Rep"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    status = models.CharField(
        _("Status"), max_length=2, default="PD", choices=DUKA_STORE_STATUS_CHOICES
    )
    date_of_confirmation = models.DateTimeField(null=True, blank=True)
    latest_outlet_latitude = models.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        null=True,
        blank=True,
    )
    latest_outlet_longitude = models.FloatField(
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        null=True,
        blank=True,
    )
    route_name = models.CharField(max_length=30, null=True, blank=True)
    align_code = models.CharField(max_length=30, null=True, blank=True)
    phone_number = models.BigIntegerField(null=True, blank=True)
    onboard = models.BooleanField(_("Onboarded to Kasha"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        get_user_model(), on_delete=models.DO_NOTHING, null=True, blank=True
    )

    def __str__(self) -> str:
        return str(self.outlet_code)

    class Meta:
        verbose_name = _("Duka's Outlet")
        verbose_name_plural = _("Duka's Outlets")

    def clean(self):
        if self.phone_number:
            if self._state.adding:
                phone_number_exists = Outlet.objects.filter(
                    phone_number=self.phone_number
                ).exists()
                if phone_number_exists:
                    raise ValidationError(
                        _("Phone number already exists in the system")
                    )
            else:
                phone_number_exists = (
                    Outlet.objects.filter(phone_number=self.phone_number)
                    .exclude(id=self.id)
                    .exists()
                )
                if phone_number_exists:
                    raise ValidationError(
                        _("Phone number already exists in the system")
                    )

            valid = clean_phone_number(self.phone_number)
            if not valid:
                raise ValidationError(
                    {
                        "phone_number": "Phone number should be in E164 format (Kenya or Rwanda) without the + sign"
                    }
                )

    def save(self, **kwargs):
        self.full_clean()
        return super().save(**kwargs)


is_alphanumeric = RegexValidator(
    r"^[0-9a-zA-Z]*$", "Only alphanumeric characters are allowed."
)


class Payment(models.Model):
    order_id = models.CharField(max_length=255, validators=[is_alphanumeric])
    outlet = models.ForeignKey(Outlet, on_delete=models.SET_NULL, null=True, blank=True)
    amount_auth = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, choices=CURRENCY_CHOICES, default="KES")
    pre_auth_request_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    amount_requested = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    payment_request_date = models.DateTimeField(null=True, blank=True)
    payment_request_status = models.CharField(max_length=50, null=True, blank=True)
    payment_status = models.CharField(max_length=50, null=True, blank=True)
    pre_auth_status = models.CharField(max_length=50, null=True, blank=True)
    pre_auth_confirmation_status = models.CharField(
        max_length=50, null=True, blank=True
    )
    cs_agent = models.ForeignKey(
        get_user_model(), on_delete=models.DO_NOTHING, null=True, blank=True
    )
    pre_auth_verified = models.BooleanField(default=False)
    refunded = models.BooleanField(default=False)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["order_id"],
                condition=Q(payment_status="APPROVED"),
                name="Unique approved payment",
            )
        ]

    def __str__(self) -> str:
        return str(self.id)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class PaymentLog(models.Model):
    payment_id = models.ForeignKey(Payment, on_delete=models.CASCADE)
    pre_auth_response = models.JSONField(null=True, blank=True)
    pre_auth_batch_id = models.CharField(max_length=400, null=True, blank=True)
    pre_auth_get_response = models.JSONField(null=True, blank=True)
    charge_request_response = models.JSONField(null=True, blank=True)
    charge_request_batch_id = models.CharField(max_length=400, null=True, blank=True)
    charge_request_get_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    post_failure_log = models.JSONField(null=True, blank=True)
    get_failure_log = models.JSONField(null=True, blank=True)

    def __str__(self) -> str:
        return str(self.id)


class Refund(models.Model):
    payment_id = models.ForeignKey(Payment, on_delete=models.CASCADE)
    currency = models.CharField(max_length=5, choices=CURRENCY_CHOICES, default="KES")
    refunded_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    refund_requested_at = models.DateTimeField(auto_now_add=True)
    refund_auth_status = models.CharField(max_length=30, null=True, blank=True)
    refund_confirm_status = models.CharField(max_length=30, null=True, blank=True)
    cs_agent = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)

    def __str__(self) -> str:
        return str(self.payment_id)


class RefundLog(models.Model):
    payment_id = models.ForeignKey(Payment, on_delete=models.CASCADE)
    post_request_response = models.JSONField(null=True, blank=True)
    get_request_response = models.JSONField(null=True, blank=True)
    refund_batch_id = models.CharField(max_length=400, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.payment_id)


class Document(models.Model):
    document = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True, blank=True)
    uploaded_by = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)

    def __str__(self):
        return str(self.id)
