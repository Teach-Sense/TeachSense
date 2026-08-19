"""
API Views for Device endpoints.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from apps.devices.models import Device
from apps.devices.api.serializers import (
    DeviceListSerializer,
    DeviceDetailSerializer,
    DeviceRegisterSerializer,
)
from common.responses import APIResponse
from common.pagination import StandardResultsSetPagination


class DeviceRegisterView(APIView):
    """
    Register a new device (simplified, no token required).
    POST /api/devices/register/
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = DeviceRegisterSerializer(data=request.data)
        if serializer.is_valid():
            device = serializer.save()
            return APIResponse.created(
                data={
                    "device_id": device.device_id,
                    "status": "registered",
                },
                message="Device registered successfully.",
            )
        return APIResponse.validation_error(
            errors=serializer.errors,
            message="Failed to register device.",
        )


class DeviceListView(APIView):
    """
    List all devices.
    GET /api/devices/
    """

    permission_classes = [AllowAny]

    def get(self, request):
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

    permission_classes = [AllowAny]

    def get(self, request, device_id):
        device = get_object_or_404(Device, id=device_id)
        serializer = DeviceDetailSerializer(device)
        return APIResponse.success(data=serializer.data)
