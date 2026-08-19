"""
Serializers for Session API.
"""
from rest_framework import serializers
from apps.lectures.models import Session
from apps.lecturers.models import Lecturer
from apps.summaries.models import Summary
from apps.analytics.models import SessionAnalytics


class LecturerSerializer(serializers.ModelSerializer):
    """Serializer for Lecturer model."""

    class Meta:
        model = Lecturer
        fields = (
            "id",
            "user",
            "overall_effectiveness_score",
            "average_student_comprehension",
            "department",
        )


class SummarySerializer(serializers.ModelSerializer):
    """Serializer for Summary model."""

    class Meta:
        model = Summary
        fields = (
            "id",
            "structured_summary",
            "key_concepts",
            "important_points",
            "accuracy_score",
            "model_agreement_score",
            "models_used",
        )


class SessionAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for SessionAnalytics model."""

    class Meta:
        model = SessionAnalytics
        fields = (
            "total_questions",
            "evaluated_responses",
            "average_accuracy",
            "average_completeness",
            "average_clarity",
            "overall_effectiveness",
            "summary_confidence",
            "engagement_score",
            "insights",
        )


class SessionListSerializer(serializers.ModelSerializer):
    """Serializer for listing sessions (brief)."""

    lecture = LecturerSerializer(read_only=True, source="lecturer")
    analytics = SessionAnalyticsSerializer(read_only=True)

    class Meta:
        model = Session
        fields = (
            "id",
            "lecture",
            "title",
            "class_taught",
            "status",
            "transcript_ready",
            "summary_ready",
            "questions_ready",
            "evaluation_ready",
            "results_published",
            "teaching_effectiveness_score",
            "average_student_comprehension",
            "teaching_scope_score",
            "started_at",
            "ended_at",
            "analytics",
        )


class SessionDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed session view."""

    lecture = LecturerSerializer(read_only=True, source="lecturer")
    summary = SummarySerializer(read_only=True)
    analytics = SessionAnalyticsSerializer(read_only=True)

    class Meta:
        model = Session
        fields = (
            "id",
            "lecture",
            "title",
            "description",
            "class_taught",
            "status",
            "transcript_ready",
            "summary_ready",
            "questions_ready",
            "evaluation_ready",
            "results_published",
            "teaching_effectiveness_score",
            "average_student_comprehension",
            "teaching_scope_score",
            "tips",
            "summary",
            "analytics",
            "started_at",
            "ended_at",
            "created_at",
            "updated_at",
        )


class SessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new session."""

    class Meta:
        model = Session
        fields = ("lecturer", "title", "description", "class_taught")

    lecture = serializers.PrimaryKeyRelatedField(
        source="lecturer",
        queryset=Lecturer.objects.all(),
        required=False,
        allow_null=True,
    )

    def create(self, validated_data):
        """Create session with lecturer context."""
        return Session.objects.create(**validated_data)


class SessionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating session."""

    class Meta:
        model = Session
        fields = ("title", "description", "class_taught", "status", "tips")
