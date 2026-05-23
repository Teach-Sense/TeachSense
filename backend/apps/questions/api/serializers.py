"""
Serializers for Question API.
"""
from rest_framework import serializers
from apps.questions.models import Question


class QuestionListSerializer(serializers.ModelSerializer):
    """Serializer for listing questions."""

    class Meta:
        model = Question
        fields = (
            "id",
            "session",
            "order",
            "question_text",
            "difficulty_level",
            "ensemble_agreement_score",
            "ensemble_confidence_score",
            "created_at",
        )


class QuestionDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed question view."""

    class Meta:
        model = Question
        fields = (
            "id",
            "session",
            "order",
            "question_text",
            "model_answer",
            "difficulty_level",
            "ensemble_agreement_score",
            "ensemble_confidence_score",
            "audio_file",
            "created_at",
            "updated_at",
        )


class QuestionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating question."""

    class Meta:
        model = Question
        fields = (
            "session",
            "order",
            "question_text",
            "model_answer",
            "difficulty_level",
        )
