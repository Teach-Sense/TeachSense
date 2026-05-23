"""
Serializers for Transcript API.
"""
from rest_framework import serializers
from apps.transcripts.models import Transcript


class TranscriptListSerializer(serializers.ModelSerializer):
    """Serializer for listing transcripts."""

    class Meta:
        model = Transcript
        fields = (
            "id",
            "session",
            "confidence_score",
            "preprocessed",
            "created_at",
        )


class TranscriptDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed transcript view."""

    class Meta:
        model = Transcript
        fields = (
            "id",
            "session",
            "transcript_text",
            "confidence_score",
            "preprocessed",
            "created_at",
            "updated_at",
        )


class TranscriptCreateSerializer(serializers.ModelSerializer):
    """Serializer for uploading transcript."""

    class Meta:
        model = Transcript
        fields = ("session", "transcript_text", "confidence_score")

    def create(self, validated_data):
        """Create transcript and queue processing."""
        transcript = Transcript.objects.create(**validated_data)
        
        # Queue lecture processing task
        from apps.lectures.tasks import process_lecture_session
        process_lecture_session.delay(transcript.session.id)
        
        return transcript
