"""
Admin configuration for Devices app.
"""
from django.contrib import admin
from apps.devices.models import Device, DeviceSyncLog


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Admin view for Device model."""

    list_display = (
        "device_name",
        "device_id",
        "device_type",
        "status",
        "location",
        "last_sync",
        "is_active",
    )
    list_filter = ("device_type", "status", "is_active", "created_at")
    search_fields = ("device_name", "device_id", "location")
    readonly_fields = ("id", "device_token", "created_at", "updated_at")
    fieldsets = (
        ("Device Information", {
            "fields": ("id", "device_id", "device_name", "device_type", "location")
        }),
        ("System Information", {
            "fields": ("os_type", "os_version", "app_version")
        }),
        ("Authentication", {
            "fields": ("device_token",)
        }),
        ("Status", {
            "fields": ("status", "is_active", "last_sync", "last_sync_status")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(DeviceSyncLog)
class DeviceSyncLogAdmin(admin.ModelAdmin):
    """Admin view for DeviceSyncLog model."""

    list_display = (
        "device",
        "sync_type",
        "status",
        "items_pulled",
        "items_pushed",
        "sync_duration_ms",
        "created_at",
    )
    list_filter = ("sync_type", "status", "created_at")
    search_fields = ("device__device_name", "device__device_id")
    readonly_fields = ("created_at",)
    fieldsets = (
        ("Device", {
            "fields": ("device",)
        }),
        ("Sync Information", {
            "fields": ("sync_type", "status", "items_pulled", "items_pushed", "sync_duration_ms")
        }),
        ("Error Details", {
            "fields": ("error_message",),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )
