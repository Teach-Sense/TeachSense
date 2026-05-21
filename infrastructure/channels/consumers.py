"""
WebSocket consumers for real-time updates.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from apps.lectures.models import Session


class SessionConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for session real-time updates.
    Connects: ws://host/ws/sessions/<session_id>/
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.session_group_name = f"session_{self.session_id}"

        # Join session group
        await self.channel_layer.group_add(self.session_group_name, self.channel_name)
        await self.accept()

        # Send confirmation
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connected",
                    "message": f"Connected to session {self.session_id}",
                    "session_id": self.session_id,
                }
            )
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.session_group_name, self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(text_data)
            message_type = data.get("type", "ping")

            if message_type == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))
            elif message_type == "subscribe":
                # Subscribe to specific updates
                await self.channel_layer.group_send(
                    self.session_group_name,
                    {
                        "type": "session_update",
                        "message": f"User subscribed to updates",
                    },
                )
        except json.JSONDecodeError:
            pass

    # Receive message from group
    async def session_update(self, event):
        """Broadcast session update to WebSocket."""
        message = event.get("message", "")
        data = event.get("data", {})

        await self.send(
            text_data=json.dumps(
                {
                    "type": "session_update",
                    "message": message,
                    "data": data,
                }
            )
        )

    async def question_ready(self, event):
        """Broadcast when questions are ready."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "questions_ready",
                    "session_id": self.session_id,
                    "questions": event.get("questions", []),
                }
            )
        )

    async def response_submitted(self, event):
        """Broadcast when response is submitted."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "response_submitted",
                    "session_id": self.session_id,
                    "question_id": event.get("question_id"),
                    "response_count": event.get("response_count"),
                }
            )
        )

    async def evaluation_complete(self, event):
        """Broadcast when evaluation is complete."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "evaluation_complete",
                    "session_id": self.session_id,
                    "analytics": event.get("analytics", {}),
                }
            )
        )

    async def results_published(self, event):
        """Broadcast when results are published."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "results_published",
                    "session_id": self.session_id,
                    "message": "Session results are now available",
                }
            )
        )


class DashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for dashboard real-time updates.
    Connects: ws://host/ws/dashboard/
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.dashboard_group_name = "dashboard_updates"

        # Join dashboard group
        await self.channel_layer.group_add(self.dashboard_group_name, self.channel_name)
        await self.accept()

        # Send confirmation
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connected",
                    "message": "Connected to dashboard updates",
                }
            )
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.dashboard_group_name, self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(text_data)
            message_type = data.get("type", "ping")

            if message_type == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))
        except json.JSONDecodeError:
            pass

    # Receive message from group
    async def dashboard_update(self, event):
        """Broadcast dashboard update."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "dashboard_update",
                    "message": event.get("message", ""),
                    "data": event.get("data", {}),
                }
            )
        )

    async def session_created(self, event):
        """Broadcast when new session is created."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "session_created",
                    "session": event.get("session", {}),
                }
            )
        )

    async def session_completed(self, event):
        """Broadcast when session is completed."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "session_completed",
                    "session_id": event.get("session_id"),
                    "effectiveness_score": event.get("effectiveness_score"),
                }
            )
        )
