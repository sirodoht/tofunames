from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjUserAdmin

from main import models

admin.site.site_header = "tofunames admin"


@admin.register(models.User)
class UserAdmin(DjUserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "created_at",
        "last_login",
    )
    list_display_links = ("id", "username")

    fieldsets = (
        (None, {"fields": ("username", "password", "email")}),
        ("Important dates", {"fields": ("last_login", "created_at")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    readonly_fields = ("created_at",)
    search_fields = ("username", "email")
    ordering = ["-id"]


@admin.register(models.Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "first_name",
        "last_name",
        "owner",
        "api_id",
        "created_at",
    )
    ordering = ["-id"]


@admin.register(models.Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "domain_name",
        "contact",
        "owner",
        "created_at",
    )
    ordering = ["-id"]


@admin.register(models.Checkout)
class CheckoutAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "domain",
        "created_at",
    )
    ordering = ["-id"]
