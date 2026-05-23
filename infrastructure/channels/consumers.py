"""
Django Channels consumers for real-time WebSocket communication.

Handles live session updates, dashboard metrics, and interactive feedback.
"""
import json
import logging
from typing import Any, Dict

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class SessionConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for live session updates.
    
    Handles:
    - Live transcript streaming
    - Real-time question updates
    - Student response feedback
    - Session status changes
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.room_group_name = f"session_{self.session_id}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        logger.info(f"SessionConsumer connected for session {self.session_id}")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        logger.info(f"SessionConsumer disconnected for session {self.session_id}")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            event_type = data.get("type")

            if event_type == "transcript_update":
                await self.handle_transcript_update(data)
            elif event_type == "question_update":
                await self.handle_question_update(data)
            elif event_type == "response_feedback":
                await self.handle_response_feedback(data)
            else:
                logger.warning(f"Unknown event type: {event_type}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            await self.send_error("Invalid JSON format")

    async def handle_transcript_update(self, data: Dict[str, Any]):
        """Broadcast transcript updates to all clients in session."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "transcript.update",
                "transcript_segment": data.get("segment"),
                "timestamp": data.get("timestamp"),
            },
        )

    async def handle_question_update(self, data: Dict[str, Any]):
        """Broadcast question updates to all clients in session."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "question.update",
                "question": data.get("question"),
                "question_id": data.get("question_id"),
            },
        )

    async def handle_response_feedback(self, data: Dict[str, Any]):
        """Broadcast response feedback to all clients in session."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "response.feedback",
                "response_id": data.get("response_id"),
                "feedback": data.get("feedback"),
                "score": data.get("score"),
            },
        )

    # Event handlers (called by channel layer)
    async def transcript_update(self, event):
        """Send transcript update to WebSocket."""
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
        """Send question update to WebSocket."""
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
        """Send response feedback to WebSocket."""
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
        """Send error message to client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "message": message,
                }
            )
        )


class DashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time dashboard updates.
    
    Handles:
    - Live metrics and analytics
    - Session statistics
    - Performance indicators
    - Student engagement tracking
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.room_group_name = "dashboard_live"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        logger.info("DashboardConsumer connected")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        logger.info("DashboardConsumer disconnected")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            event_type = data.get("type")

            if event_type == "subscribe_metrics":
                await self.handle_subscribe_metrics(data)
            elif event_type == "subscribe_sessions":
                await self.handle_subscribe_sessions(data)
            else:
                logger.warning(f"Unknown event type: {event_type}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            await self.send_error("Invalid JSON format")

    async def handle_subscribe_metrics(self, data: Dict[str, Any]):
        """Subscribe to real-time metrics updates."""
        metrics_type = data.get("metrics_type")  # e.g., "engagement", "performance"
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "metrics.update",
                "metrics_type": metrics_type,
                "data": data.get("data"),
            },
        )

    async def handle_subscribe_sessions(self, data: Dict[str, Any]):
        """Subscribe to active sessions updates."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "sessions.update",
                "data": data.get("data"),
            },
        )

    # Event handlers (called by channel layer)
    async def metrics_update(self, event):
        """Send metrics update to WebSocket."""
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
        """Send sessions update to WebSocket."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "sessions_update",
                    "data": event["data"],
                }
            )
        )

    async def send_error(self, message: str):
        """Send error message to client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "message": message,
                }
            )
        )
