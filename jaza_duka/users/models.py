from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

now = timezone.now()


class UserSoftDeleteManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(delete_user__isnull=True)


class User(AbstractUser):
    """Default user for jaza_duka."""

    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    delete_user = models.DateTimeField(
        _("Delete this User"), null=True, blank=True, default=None
    )
    first_name = None  # type: ignore
    last_name = None  # type: ignore

    objects = UserSoftDeleteManager()
    all_objects = models.Manager()

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})

    def delete(self):
        self.delete_user = timezone.now()
        self.save()
