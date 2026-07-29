"""
API Views for Device endpoints.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.devices.models import Device, DeviceSyncLog
from apps.devices.api.serializers import (
    DeviceListSerializer,
    DeviceDetailSerializer,
    DeviceRegisterSerializer,
    DeviceSyncResponseSerializer,
)
from common.responses import APIResponse
from common.permissions import IsDeviceAuthenticated
from common.pagination import StandardResultsSetPagination


class DeviceRegisterView(APIView):
    """
    Register a new device.
    POST /api/devices/register/
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Register new device and generate token."""
        serializer = DeviceRegisterSerializer(data=request.data)
        if serializer.is_valid():
            device = serializer.save()
            return APIResponse.created(
                data={
                    "device_id": device.device_id,
                    "device_token": device.device_token,
                    "sync_interval_seconds": 30,
                    "status": "registered",
                },
                message="Device registered successfully.",
            )

        return APIResponse.validation_error(
            errors=serializer.errors,
            message="Failed to register device.",
        )


class DeviceSyncView(APIView):
    """
    Device synchronization endpoint.
    GET /api/devices/sync/
    POST /api/devices/sync/
    """

    permission_classes = [IsDeviceAuthenticated]

    def get(self, request):
        """Pull data from cloud to device."""
        device = request.device
        
        # Mark device as online
        device.mark_online()
        device.last_sync_status = "sync_pull_started"
        device.save()

        # Return data for device to process
        from apps.lectures.models import Session
        from apps.sessions.api.serializers import SessionListSerializer
        from apps.questions.api.serializers import QuestionListSerializer
        from apps.questions.models import Question

        # Fetch active sessions
        sessions = Session.objects.filter(status="completed", questions_ready=True)[:10]
        questions = Question.objects.filter(session__in=sessions)[:50]

        response_data = {
            "device_id": device.device_id,
            "status": "success",
            "sync_interval_seconds": 30,
            "last_sync": device.last_sync,
            "sessions": SessionListSerializer(sessions, many=True).data,
            "questions": QuestionListSerializer(questions, many=True).data,
            "responses_to_submit": [],  # Device would submit responses here
            "commands": [],  # Future: remote commands
        }

        # Log sync
        DeviceSyncLog.objects.create(
            device=device,
            sync_type="pull",
            status="success",
            items_pulled=len(questions),
        )

        return APIResponse.success(data=response_data)

    def post(self, request):
        """Push data from device to cloud."""
        device = request.device
        
        # Mark device as online
        device.mark_online()
        device.last_sync_status = "sync_push_completed"
        device.save()

        # Process responses from device
        responses_data = request.data.get("responses", [])
        items_pushed = len(responses_data)

        # TODO: Process and save responses from device

        # Log sync
        DeviceSyncLog.objects.create(
            device=device,
            sync_type="push",
            status="success",
            items_pushed=items_pushed,
        )

        return APIResponse.success(
            data={
                "status": "success",
                "items_processed": items_pushed,
                "next_sync_seconds": 30,
            },
            message=f"Processed {items_pushed} items from device.",
        )


class DeviceListView(APIView):
    """
    List all registered devices (admin only).
    GET /api/devices/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all devices."""
        # Check if user is admin
        if not request.user.is_superuser:
            return APIResponse.forbidden("Only admins can view all devices.")

        devices = Device.objects.all()
        paginator = StandardResultsSetPagination()
        paginated = paginator.paginate_queryset(devices, request)
        serializer = DeviceListSerializer(paginated, many=True)

        return Response(paginator.get_paginated_response(serializer.data))


class DeviceDetailView(APIView):
    """
    Get device details.
    GET /api/devices/<device_id>/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, device_id):
        """Get device details."""
        # Check if user is admin or device owner
        if not request.user.is_superuser:
            return APIResponse.forbidden("Only admins can view device details.")

        device = get_object_or_404(Device, id=device_id)
        serializer = DeviceDetailSerializer(device)
        return APIResponse.success(data=serializer.data)


class DeviceCommandView(APIView):
    """
    Send a command to a device.
    POST /api/devices/{id}/command/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, device_id):
        command = request.data.get("command")
        parameters = request.data.get("parameters", {})
        device = get_object_or_404(Device, id=device_id)
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"device_{device.device_id}",
            {
                "type": "device_command",
                "command": command,
                "parameters": parameters,
            },
        )
        return APIResponse.success(
            data={
                "command_id": f"cmd_{device.device_id}",
                "status": "executed",
                "command": command,
                "parameters": parameters,
            }
        )


class DeviceStatusView(APIView):
    """
    Get device status.
    GET /api/devices/<device_id>/status/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, device_id):
        """Get device status."""
        if not request.user.is_superuser:
            return APIResponse.forbidden("Only admins can view device status.")

        device = get_object_or_404(Device, id=device_id)

        is_online = device.status == "online"
        time_since_sync = (timezone.now() - device.last_sync).total_seconds() if device.last_sync else None

        return APIResponse.success(
            data={
                "device_id": device.device_id,
                "device_name": device.device_name,
                "status": device.status,
                "is_online": is_online,
                "last_sync": device.last_sync,
                "seconds_since_sync": time_since_sync,
                "last_sync_status": device.last_sync_status,
            }
        )
