"""
URL routing for Devices API.
"""
from django.urls import path
from apps.devices.api.views import (
    DeviceRegisterView,
    DeviceSyncView,
    DeviceListView,
    DeviceDetailView,
    DeviceStatusView,
)

app_name = "devices-api"

urlpatterns = [
    # Device management
    path("register/", DeviceRegisterView.as_view(), name="device-register"),
    path("sync/", DeviceSyncView.as_view(), name="device-sync"),
    path("", DeviceListView.as_view(), name="device-list"),
    path("<uuid:device_id>/", DeviceDetailView.as_view(), name="device-detail"),
    path("<uuid:device_id>/status/", DeviceStatusView.as_view(), name="device-status"),
]
