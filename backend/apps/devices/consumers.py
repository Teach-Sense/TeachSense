"""
Device WebSocket consumer.

Accepts connections from registered classroom devices (ESP32, tablets, etc.).
Each device authenticates with a token, then exchanges protocol messages:
- handshake / handshake_response
- register_session / session_confirmed
- start_recording / recording_started / recording_stopped
- new_question / question_acknowledged
- listen_for_answers / listening_started
- audio_frame / acknowledge
- device_status / status_acknowledged
- error
"""

import json
import logging
from typing import Any, Dict

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.devices.models import Device

logger = logging.getLogger(__name__)


class DeviceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.token = self.scope["query_string"].decode().split("token=")[-1] if "token=" in self.scope["query_string"].decode() else ""
        self.device = await self.get_device_by_token(self.token)
        if not self.device:
            await self.close(code=4001)
            return

        self.room_group_name = f"device_{self.device.device_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.send(
            text_data=json.dumps(
                {
                    "type": "handshake_response",
                    "status": "accepted",
                    "device_status": "connected",
                }
            )
        )

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            event_type = data.get("type")
            handler = {
                "register_session": self.handle_register_session,
                "device_status": self.handle_device_status,
                "audio_frame": self.handle_audio_frame,
                "command_result": self.handle_command_result,
                "error": self.handle_error,
            }.get(event_type)

            if handler:
                await handler(data)
            else:
                await self.send_error(f"Unknown message type: {event_type}")
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")

    async def handle_register_session(self, data: Dict[str, Any]):
        session_id = data.get("session_id")
        await self.send(
            text_data=json.dumps(
                {
                    "type": "session_confirmed",
                    "session_id": session_id,
                    "status": "ready",
                }
            )
        )

    async def handle_device_status(self, data: Dict[str, Any]):
        await database_sync_to_async(self._update_device_status)(data)
        await self.send(
            text_data=json.dumps(
                {
                    "type": "status_acknowledged",
                    "timestamp": data.get("timestamp"),
                }
            )
        )

    async def handle_audio_frame(self, data: Dict[str, Any]):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "acknowledge",
                    "frame_number": data.get("frame_number"),
                    "timestamp": data.get("timestamp"),
                }
            )
        )

    async def handle_command_result(self, data: Dict[str, Any]):
        logger.info("Device command result: %s", data)

    async def handle_error(self, data: Dict[str, Any]):
        logger.error("Device error: %s", data)

    async def device_command(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": event["command"],
                    "parameters": event.get("parameters", {}),
                }
            )
        )

    async def send_error(self, message: str):
        await self.send(text_data=json.dumps({"type": "error", "message": message}))

    def _update_device_status(self, data: Dict[str, Any]):
        device = self.device
        device.status = data.get("status", device.status)
        if data.get("cpu_usage") is not None:
            device.cpu_usage = data["cpu_usage"]
        if data.get("memory_usage") is not None:
            device.memory_usage = data["memory_usage"]
        device.save(update_fields=["status", "cpu_usage", "memory_usage", "updated_at"])

    @database_sync_to_async
    def get_device_by_token(self, token: str) -> Device | None:
        try:
            return Device.objects.get(device_token=token)
        except Device.DoesNotExist:
            return None
