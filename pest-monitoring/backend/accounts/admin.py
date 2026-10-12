from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class PestUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "district", "is_active")
    list_filter = ("role", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Pest Monitoring", {"fields": ("role", "entra_object_id", "postcode", "district", "consent_to_updates")}),
    )
