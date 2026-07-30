"""
Serializers for Device API.
"""
from rest_framework import serializers
from apps.devices.models import Device, DeviceSyncLog


class DeviceSyncLogSerializer(serializers.ModelSerializer):
    """Serializer for device sync logs."""

    class Meta:
        model = DeviceSyncLog
        fields = (
            "id",
            "sync_type",
            "status",
            "items_pulled",
            "items_pushed",
            "sync_duration_ms",
            "error_message",
            "created_at",
        )


class DeviceListSerializer(serializers.ModelSerializer):
    """Serializer for listing devices."""

    class Meta:
        model = Device
        fields = (
            "id",
            "device_id",
            "device_name",
            "device_type",
            "location",
            "status",
            "last_sync",
            "is_active",
        )


class DeviceDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed device view."""

    sync_logs = DeviceSyncLogSerializer(read_only=True, many=True)

    class Meta:
        model = Device
        fields = (
            "id",
            "device_id",
            "device_name",
            "device_type",
            "location",
            "device_token",
            "os_type",
            "os_version",
            "app_version",
            "status",
            "last_sync",
            "last_sync_status",
            "is_active",
            "sync_logs",
            "created_at",
            "updated_at",
        )


class DeviceRegisterSerializer(serializers.ModelSerializer):
    """Serializer for device registration."""

    class Meta:
        model = Device
        fields = ("device_id", "device_name", "device_type", "location", "os_type", "os_version", "app_version")

    def create(self, validated_data):
        """Create device with auto-generated token."""
        import uuid
        device_token = str(uuid.uuid4())
        validated_data["device_token"] = device_token
        validated_data["status"] = "online"
        return Device.objects.create(**validated_data)


class DeviceSyncRequestSerializer(serializers.Serializer):
    """Serializer for device sync request."""

    last_sync = serializers.DateTimeField(required=False)
    sync_type = serializers.ChoiceField(choices=["pull", "push", "bidirectional"])


class DeviceSyncResponseSerializer(serializers.Serializer):
    """Serializer for device sync response."""

    device_id = serializers.CharField()
    status = serializers.CharField()
    sync_interval_seconds = serializers.IntegerField()
    sessions = serializers.ListField()
    questions = serializers.ListField()
    responses_to_submit = serializers.ListField()
    commands = serializers.ListField()
