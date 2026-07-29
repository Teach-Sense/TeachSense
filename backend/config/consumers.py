"""
Django Channels consumers for the deployed backend package.
"""

import json
import logging
from typing import Any, Dict

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class SessionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.room_group_name = f"session_{self.session_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            event_type = data.get("type")

            if event_type == "transcript_update":
                await self.handle_transcript_update(data)
            elif event_type == "question_update":
                await self.handle_question_update(data)
            elif event_type == "response_feedback":
                await self.handle_response_feedback(data)
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")

    async def handle_transcript_update(self, data: Dict[str, Any]):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "transcript.update",
                "transcript_segment": data.get("segment"),
                "timestamp": data.get("timestamp"),
            },
        )

    async def handle_question_update(self, data: Dict[str, Any]):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "question.update",
                "question": data.get("question"),
                "question_id": data.get("question_id"),
            },
        )

    async def handle_response_feedback(self, data: Dict[str, Any]):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "response.feedback",
                "response_id": data.get("response_id"),
                "feedback": data.get("feedback"),
                "score": data.get("score"),
            },
        )

    async def transcript_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "transcript_update",
                    "segment": event["transcript_segment"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    async def question_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "question_update",
                    "question": event["question"],
                    "question_id": event["question_id"],
                }
            )
        )

    async def response_feedback(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "response_feedback",
                    "response_id": event["response_id"],
                    "feedback": event["feedback"],
                    "score": event["score"],
                }
            )
        )

    async def send_error(self, message: str):
        await self.send(text_data=json.dumps({"type": "error", "message": message}))


class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "dashboard_live"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            event_type = data.get("type")

            if event_type == "subscribe_metrics":
                await self.handle_subscribe_metrics(data)
            elif event_type == "subscribe_sessions":
                await self.handle_subscribe_sessions(data)
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")

    async def handle_subscribe_metrics(self, data: Dict[str, Any]):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "metrics.update",
                "metrics_type": data.get("metrics_type"),
                "data": data.get("data"),
            },
        )

    async def handle_subscribe_sessions(self, data: Dict[str, Any]):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "sessions.update",
                "data": data.get("data"),
            },
        )

    async def metrics_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "metrics_update",
                    "metrics_type": event["metrics_type"],
                    "data": event["data"],
                }
            )
        )

    async def sessions_update(self, event):
        await self.send(text_data=json.dumps({"type": "sessions_update", "data": event["data"]}))

    async def send_error(self, message: str):
        await self.send(text_data=json.dumps({"type": "error", "message": message}))

        
class DeviceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.device_id = self.scope["url_route"]["kwargs"]["device_token"]
        self.room_group_name = f"device_{self.device_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            event_type = data.get("type")

            if event_type == "handshake":
                await self.handle_handshake(data)
            elif event_type == "audio_frame":
                await self.handle_audio_frame(data)
            elif event_type == "heartbeat":
                await self.handle_heartbeat(data)
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")

    async def handle_handshake(self, data: Dict[str, Any]):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "handshake_ack",
                    "device_id": self.device_id,
                    "status": "connected",
                }
            )
        )

    async def handle_audio_frame(self, data: Dict[str, Any]):
        session_id = data.get("session_id")
        if session_id is None:
            await self.send_error("session_id is required for audio_frame")
            return

        await self.channel_layer.group_send(
            f"session_{session_id}",
            {
                "type": "audio.frame",
                "device_id": self.device_id,
                "timestamp": data.get("timestamp"),
                "data_base64": data.get("data_base64"),
            },
        )

    async def handle_heartbeat(self, data: Dict[str, Any]):
        await self.send(text_data=json.dumps({"type": "heartbeat_ack"}))

    async def audio_frame(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "audio_frame",
                    "device_id": event["device_id"],
                    "timestamp": event["timestamp"],
                    "data_base64": event["data_base64"],
                }
            )
        )

    async def send_error(self, message: str):
        await self.send(text_data=json.dumps({"type": "error", "message": message}))