"""
Django Channels consumers for the deployed backend package.
"""

import asyncio
import base64
import json
import logging
import os
import tempfile
import wave
from typing import Any, Dict

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from openai import OpenAI

from apps.lectures.models import Session

logger = logging.getLogger(__name__)

_openai_client = None


def get_openai_client():
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


class SessionConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for device-to-server communication during a lecture session.
    Handles audio streaming, question delivery, and response collection.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.session = None
        self.device_id = None
        self.audio_chunks = []
        self.is_recording = False
        self.question_index = 0
        self.questions = []
        self.question_responses = []

    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.room_group_name = f"session_{self.session_id}"

        try:
            self.session = await sync_to_async(Session.objects.get)(id=self.session_id)
        except Session.DoesNotExist:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.send_json({"type": "connected", "session_id": self.session_id})

    async def disconnect(self, close_code):
        if self.room_group_name:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                data = json.loads(text_data)
                event_type = data.get("type")
                if event_type == "start_recording":
                    await self.handle_start_recording(data)
                elif event_type == "stop_recording":
                    await self.handle_stop_recording()
                elif event_type == "response":
                    await self.handle_response(data)
                elif event_type == "ping":
                    await self.send_json({"type": "pong"})
            except json.JSONDecodeError:
                await self.send_error("Invalid JSON format")
        elif bytes_data:
            await self.handle_audio_chunk(bytes_data)

    async def handle_start_recording(self, data: Dict[str, Any]):
        self.device_id = data.get("device_id")
        topic = data.get("topic")
        class_taught = data.get("class_taught")

        if topic:
            self.session.title = topic
        if class_taught:
            self.session.class_taught = class_taught

        self.session.status = "recording"
        self.session.started_at = timezone.now()
        await sync_to_async(self.session.save)()

        self.is_recording = True
        self.audio_chunks = []
        await self.send_json({"type": "recording_started"})

    async def handle_audio_chunk(self, chunk: bytes):
        if not self.is_recording:
            return
        self.audio_chunks.append(chunk)

    async def handle_stop_recording(self):
        if not self.is_recording:
            return

        self.is_recording = False
        self.session.status = "processing"
        self.session.ended_at = timezone.now()
        self.session.duration_seconds = int(
            (self.session.ended_at - self.session.started_at).total_seconds()
        )
        await sync_to_async(self.session.save)()

        await self.send_json({"type": "recording_stopped", "status": "processing"})

        try:
            transcript = await self._transcribe_audio()
            self.session.transcript_ready = True
            await sync_to_async(self.session.save)()

            await self.send_json({"type": "transcript_ready", "transcript": transcript})

            await asyncio.sleep(1)

            self.questions = await self._generate_questions(transcript)
            self.session.questions_ready = True
            await sync_to_async(self.session.save)()

            await self.send_json(
                {
                    "type": "questions_ready",
                    "count": len(self.questions),
                    "questions": self.questions,
                }
            )

            await asyncio.sleep(5)

            for idx, question in enumerate(self.questions):
                await self.send_json(
                    {
                        "type": "question",
                        "index": idx + 1,
                        "total": len(self.questions),
                        "text": question,
                    }
                )
                self.question_index = idx + 1
                await asyncio.sleep(2)

            self.session.status = "awaiting_responses"
            await sync_to_async(self.session.save)()

        except Exception as exc:
            logger.exception("Processing failed for session %s", self.session_id)
            await self.send_error(f"Processing failed: {str(exc)}")
            self.session.status = "draft"
            await sync_to_async(self.session.save)()

    async def handle_response(self, data: Dict[str, Any]):
        question_idx = data.get("question_index", self.question_index)
        audio_b64 = data.get("audio")
        response_text = data.get("text", "")

        if audio_b64:
            try:
                audio_bytes = base64.b64decode(audio_b64)
                response_text = await self._transcribe_response(audio_bytes) or response_text
            except Exception:
                pass

        self.question_responses.append(
            {"question_index": question_idx, "response_text": response_text}
        )

        if len(self.question_responses) >= len(self.questions):
            await self._finalize_session()
        else:
            await self.send_json({"type": "response_received", "question_index": question_idx})

    async def _finalize_session(self):
        await self.send_json({"type": "processing_results"})

        try:
            scores = await self._calculate_scores()
            tips = await self._generate_tips()

            self.session.teaching_effectiveness_score = scores["total"]
            self.session.average_student_comprehension = scores["comprehension"]
            self.session.teaching_scope_score = scores["scope"]
            self.session.tips = tips
            self.session.status = "completed"
            self.session.results_published = True
            await sync_to_async(self.session.save)()

            await self.send_json(
                {
                    "type": "results",
                    "scores": scores,
                    "tips": tips,
                }
            )
        except Exception as exc:
            logger.exception("Finalization failed for session %s", self.session_id)
            await self.send_error(f"Results generation failed: {str(exc)}")

    async def _transcribe_audio(self) -> str:
        if not self.audio_chunks:
            return ""

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            with wave.open(tmp, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b"".join(self.audio_chunks))
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as audio_file:
                transcript = (
                    get_openai_client()
                    .audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text",
                        language="en",
                    )
                    .text
                    or ""
                ).strip()
            return transcript
        finally:
            os.unlink(tmp_path)

    async def _transcribe_response(self, audio_bytes: bytes) -> str:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            with wave.open(tmp, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_bytes)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as audio_file:
                transcript = (
                    get_openai_client()
                    .audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text",
                        language="en",
                    )
                    .text
                    or ""
                ).strip()
            return transcript
        finally:
            os.unlink(tmp_path)

    async def _generate_questions(self, transcript: str) -> list:
        if not transcript:
            return ["What was the main topic of this lecture?"]

        count = self.session.auto_question_mode or self.session.target_question_count
        if not isinstance(count, int) or count < 1:
            count = 3
        count = min(count, 5)

        prompt = (
            f"Based on the following lecture transcript, generate {count} short assessment questions. "
            "Return ONLY a valid JSON array of strings. Do not include numbering, explanations, or markdown.\n\n"
            f"Transcript:\n{transcript[:4000]}"
        )

        response = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        content = response.choices[0].message.content.strip()
        try:
            questions = json.loads(content)
            if not isinstance(questions, list):
                raise ValueError("Expected JSON array")
            return [q for q in questions if isinstance(q, str)][:count]
        except (json.JSONDecodeError, ValueError):
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            return lines[:count] or ["What was the main topic of this lecture?"]

    async def _calculate_scores(self) -> dict:
        transcript = ""
        if hasattr(self.session, "transcript") and self.session.transcript:
            transcript = self.session.transcript.full_text

        responses_text = "\n".join(
            f"Q{r['question_index']}: {r['response_text']}"
            for r in self.question_responses
        )

        prompt = (
            "You are an expert teaching evaluator. Based on the lecture transcript and student responses, "
            "rate two scores from 0-100:\n"
            "1. Student Comprehension (70% weight): How well did students understand the material?\n"
            "2. Teaching Scope (30% weight): How well did the lecture cover the intended scope?\n\n"
            f"Transcript:\n{transcript[:4000]}\n\n"
            f"Responses:\n{responses_text}\n\n"
            "Return ONLY a valid JSON object with keys: comprehension, scope, total. "
            "total = comprehension * 0.7 + scope * 0.3."
        )

        response = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        content = response.choices[0].message.content.strip()
        try:
            scores = json.loads(content)
            return {
                "comprehension": float(scores.get("comprehension", 0)),
                "scope": float(scores.get("scope", 0)),
                "total": float(scores.get("total", 0)),
            }
        except (json.JSONDecodeError, ValueError):
            return {"comprehension": 0.0, "scope": 0.0, "total": 0.0}

    async def _generate_tips(self) -> dict:
        transcript = ""
        if hasattr(self.session, "transcript") and self.session.transcript:
            transcript = self.session.transcript.full_text

        prompt = (
            "You are an expert teaching coach. Based on the lecture transcript and student responses, "
            "generate concise lecturing tips. Return ONLY a valid JSON object with these keys:\n"
            "- topics_to_revisit: array of topics students struggled with\n"
            "- explanation_tips: array of ways to explain difficult concepts better\n"
            "- top_three: array of exactly 3 actionable things to do next lecture\n\n"
            f"Transcript:\n{transcript[:4000]}\n\n"
            f"Responses:\n{chr(10).join(r['response_text'] for r in self.question_responses)}"
        )

        response = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        content = response.choices[0].message.content.strip()
        try:
            tips = json.loads(content)
            return {
                "topics_to_revisit": tips.get("topics_to_revisit", []),
                "explanation_tips": tips.get("explanation_tips", []),
                "top_three": tips.get("top_three", []),
            }
        except (json.JSONDecodeError, ValueError):
            return {
                "topics_to_revisit": [],
                "explanation_tips": [],
                "top_three": [],
            }

    async def send_json(self, data: Dict[str, Any]):
        await self.send(text_data=json.dumps(data))

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