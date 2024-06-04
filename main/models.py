from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from main import validators


class User(AbstractUser):
    first_name = None
    last_name = None
    username = models.CharField(
        _("username"),
        max_length=64,
        unique=True,
        help_text=_("Letters, digits and - only."),
        validators=[
            validators.AlphanumericHyphenValidator(),
            validators.HyphenOnlyValidator(),
        ],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id}: {self.username}"


class Contact(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    street = models.CharField(max_length=150)
    city = models.CharField(max_length=150)
    postal = models.CharField(max_length=150)
    country = models.CharField(max_length=150)
    phone = models.CharField(max_length=150)
    email = models.EmailField(max_length=150)
    api_id = models.CharField(max_length=16)
    api_log = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return f"{self.id}: {self.api_id}: {self.first_name} {self.last_name}"


class Domain(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    domain_name = models.CharField(max_length=63)
    contact = models.ForeignKey(Contact, on_delete=models.PROTECT)
    nameserver0 = models.CharField(max_length=253, blank=True, null=True, default="")
    nameserver1 = models.CharField(max_length=253, blank=True, null=True, default="")
    nameserver2 = models.CharField(max_length=253, blank=True, null=True, default="")
    nameserver3 = models.CharField(max_length=253, blank=True, null=True, default="")
    api_log = models.CharField(max_length=1000, blank=True, null=True)
    pending = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id}: {self.domain_name}"


class Checkout(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}: Checkout for {self.domain.domain_name}"
