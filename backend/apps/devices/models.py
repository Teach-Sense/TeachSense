"""
Device models for classroom hardware management.
"""
import uuid
from django.db import models


class Device(models.Model):
    """
    Represents a physical classroom device (e.g., microphone/speaker unit).
    Simplified for proof of concept: no registration required.
    """

    DEVICE_TYPE_CHOICES = [
        ("microphone_speaker", "Microphone + Speaker"),
        ("microphone", "Microphone Only"),
        ("speaker", "Speaker Only"),
        ("other", "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique device identifier",
    )
    device_name = models.CharField(max_length=255, help_text="Human-friendly device name")
    device_type = models.CharField(
        max_length=20, choices=DEVICE_TYPE_CHOICES, default="microphone_speaker"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Device"
        verbose_name_plural = "Devices"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.device_name} ({self.device_id})"
