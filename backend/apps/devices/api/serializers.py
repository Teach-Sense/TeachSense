"""
Serializers for Device API.
"""
from rest_framework import serializers
from apps.devices.models import Device


class DeviceListSerializer(serializers.ModelSerializer):
    """Serializer for listing devices."""

    class Meta:
        model = Device
        fields = (
            "id",
            "device_id",
            "device_name",
            "device_type",
            "created_at",
            "updated_at",
        )


class DeviceDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed device view."""

    class Meta:
        model = Device
        fields = (
            "id",
            "device_id",
            "device_name",
            "device_type",
            "created_at",
            "updated_at",
        )


class DeviceRegisterSerializer(serializers.ModelSerializer):
    """Serializer for device registration (simplified)."""

    class Meta:
        model = Device
        fields = ("device_id", "device_name", "device_type")

    def create(self, validated_data):
        """Create device."""
        return Device.objects.create(**validated_data)
