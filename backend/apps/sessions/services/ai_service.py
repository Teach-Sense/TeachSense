"""
AI service for lecture processing.
"""

import json
import logging
import os

from openai import OpenAI

logger = logging.getLogger(__name__)

_client = None


def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def generate_questions(transcript: str, count: int = 3) -> list:
    if not transcript:
        return ["What was the main topic of this lecture?"]

    count = max(1, min(count, 5))
    prompt = (
        f"Based on the following lecture transcript, generate {count} short assessment questions. "
        "Return ONLY a valid JSON array of strings. Do not include numbering, explanations, or markdown.\n\n"
        f"Transcript:\n{transcript[:4000]}"
    )

    response = get_client().chat.completions.create(
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


def calculate_scores(transcript: str, responses: list) -> dict:
    responses_text = "\n".join(
        f"Q{r.get('question_index', i+1)}: {r.get('response_text', '')}"
        for i, r in enumerate(responses)
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

    response = get_client().chat.completions.create(
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


def generate_tips(transcript: str, responses: list) -> dict:
    responses_text = "\n".join(
        r.get("response_text", "") for r in responses
    )

    prompt = (
        "You are an expert teaching coach. Based on the lecture transcript and student responses, "
        "generate concise lecturing tips. Return ONLY a valid JSON object with these keys:\n"
        "- topics_to_revisit: array of topics students struggled with\n"
        "- explanation_tips: array of ways to explain difficult concepts better\n"
        "- top_three: array of exactly 3 actionable things to do next lecture\n\n"
        f"Transcript:\n{transcript[:4000]}\n\n"
        f"Responses:\n{responses_text}"
    )

    response = get_client().chat.completions.create(
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
