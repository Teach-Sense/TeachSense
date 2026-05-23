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