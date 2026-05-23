"""
Serializers for Response API.
"""
from rest_framework import serializers
from apps.responses.models import Response
from apps.evaluations.models import Evaluation


class EvaluationDetailSerializer(serializers.ModelSerializer):
    """Serializer for nested evaluation details."""

    class Meta:
        model = Evaluation
        fields = (
            "id",
            "evaluator_model",
            "accuracy_assessment",
            "completeness_assessment",
            "clarity_assessment",
            "strengths",
            "areas_for_improvement",
            "created_at",
        )


class ResponseListSerializer(serializers.ModelSerializer):
    """Serializer for listing responses."""

    evaluation = EvaluationDetailSerializer(read_only=True, source="evaluation_set.first")

    class Meta:
        model = Response
        fields = (
            "id",
            "question",
            "student",
            "response_text",
            "evaluation_status",
            "accuracy_score",
            "completeness_score",
            "clarity_score",
            "overall_score",
            "ensemble_agreement_score",
            "ensemble_confidence_score",
            "evaluation",
            "created_at",
        )


class ResponseDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed response view."""

    evaluation = EvaluationDetailSerializer(read_only=True, source="evaluation_set.first")

    class Meta:
        model = Response
        fields = (
            "id",
            "question",
            "student",
            "response_text",
            "audio_file",
            "evaluation_status",
            "accuracy_score",
            "completeness_score",
            "clarity_score",
            "overall_score",
            "feedback",
            "ensemble_agreement_score",
            "ensemble_confidence_score",
            "evaluation",
            "created_at",
            "updated_at",
        )


class ResponseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating response."""

    class Meta:
        model = Response
        fields = ("question", "response_text", "audio_file")

    def create(self, validated_data):
        """Create response with student context."""
        request = self.context.get("request")
        if request and request.user:
            validated_data["student"] = request.user
        return Response.objects.create(**validated_data)


class ResponseUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating response."""

    class Meta:
        model = Response
        fields = ("response_text", "audio_file")
