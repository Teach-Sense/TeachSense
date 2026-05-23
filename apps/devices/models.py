"""
Device models for classroom hardware management.
"""
import uuid
from django.db import models
from django.utils import timezone


class Device(models.Model):
    """
    Represents a physical classroom device (e.g., tablet, smart board, laptop).
    """

    DEVICE_TYPE_CHOICES = [
        ("tablet", "Tablet"),
        ("laptop", "Laptop"),
        ("desktop", "Desktop"),
        ("smartboard", "Smart Board"),
        ("speaker", "Speaker System"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("online", "Online"),
        ("offline", "Offline"),
        ("inactive", "Inactive"),
        ("maintenance", "Maintenance"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique device identifier (MAC address or serial number)",
    )
    device_name = models.CharField(max_length=255, help_text="Human-friendly device name")
    device_type = models.CharField(
        max_length=20, choices=DEVICE_TYPE_CHOICES, default="tablet"
    )
    location = models.CharField(
        max_length=255, blank=True, help_text="Physical location (e.g., Building A, Room 101)"
    )
    device_token = models.CharField(
        max_length=255,
        unique=True,
        help_text="Authentication token for device-to-server communication",
    )

    os_type = models.CharField(
        max_length=50, blank=True, help_text="Operating system (iOS, Android, Linux, Windows)"
    )
    os_version = models.CharField(max_length=50, blank=True)
    app_version = models.CharField(max_length=50, blank=True)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="offline"
    )
    last_sync = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(
        max_length=255, blank=True, help_text="Status message from last sync"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Device"
        verbose_name_plural = "Devices"
        ordering = ["-last_sync"]

    def __str__(self):
        return f"{self.device_name} ({self.device_id})"

    def mark_online(self):
        """Mark device as online and update sync timestamp."""
        self.status = "online"
        self.last_sync = timezone.now()
        self.save(update_fields=["status", "last_sync"])

    def mark_offline(self):
        """Mark device as offline."""
        self.status = "offline"
        self.save(update_fields=["status"])


class DeviceSyncLog(models.Model):
    """
    Log of device synchronization events for debugging and monitoring.
    """

    SYNC_TYPE_CHOICES = [
        ("pull", "Pull data from cloud"),
        ("push", "Push data to cloud"),
        ("bidirectional", "Bidirectional sync"),
    ]

    STATUS_CHOICES = [
        ("success", "Success"),
        ("partial", "Partial sync"),
        ("failed", "Failed"),
    ]

    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, related_name="sync_logs"
    )
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    items_pulled = models.IntegerField(default=0)
    items_pushed = models.IntegerField(default=0)
    sync_duration_ms = models.IntegerField(
        default=0, help_text="Duration of sync in milliseconds"
    )
    
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Device Sync Log"
        verbose_name_plural = "Device Sync Logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.device.device_name} - {self.sync_type} ({self.status})"
