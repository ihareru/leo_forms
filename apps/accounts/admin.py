from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class PortalUserAdmin(UserAdmin):
    list_display = (
        "username",
        "last_name",
        "first_name",
        "position",
        "role",
        "is_active",
        "is_staff",
    )

    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    search_fields = (
        "username",
        "last_name",
        "first_name",
        "email",
        "position",
    )

    ordering = (
        "last_name",
        "first_name",
        "username",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "Портал Леовит",
            {
                "fields": (
                    "role",
                    "position",
                ),
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Портал Леовит",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "position",
                    "role",
                ),
            },
        ),
    )