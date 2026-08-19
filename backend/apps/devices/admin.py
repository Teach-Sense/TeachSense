"""
Admin configuration for Devices app.
"""
from django.contrib import admin
from apps.devices.models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Admin view for Device model."""

    list_display = (
        "device_name",
        "device_id",
        "device_type",
        "created_at",
    )
    list_filter = ("device_type", "created_at")
    search_fields = ("device_name", "device_id")
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        ("Device Information", {
            "fields": ("id", "device_id", "device_name", "device_type")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
