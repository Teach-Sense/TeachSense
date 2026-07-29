"""
ASGI config for TeachSense with Channels support.
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

# Import consumers after Django setup
from .consumers import SessionConsumer, DashboardConsumer
from apps.devices.consumers import DeviceConsumer

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(
                [
                    path("ws/sessions/<int:session_id>/", SessionConsumer.as_asgi()),
                    path("ws/dashboard/", DashboardConsumer.as_asgi()),
                    path("ws/devices/<str:device_token>/", DeviceConsumer.as_asgi()),
                ]
            )
        ),
    }
)
