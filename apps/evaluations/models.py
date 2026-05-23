from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.responses.models import Response


class Evaluation(models.Model):
    """LLM evaluation of a student response."""

    response = models.OneToOneField(
        Response,
        on_delete=models.CASCADE,
        related_name="evaluation",
        help_text="Response being evaluated",
    )
    
    # Evaluation details
    evaluator_model = models.CharField(
        max_length=100,
        help_text="Which LLM model performed evaluation",
    )
    
    # Scoring components
    accuracy_assessment = models.TextField(
        help_text="LLM assessment of accuracy",
    )
    completeness_assessment = models.TextField(
        help_text="LLM assessment of completeness",
    )
    clarity_assessment = models.TextField(
        help_text="LLM assessment of clarity",
    )
    
    # Recommendations
    strengths = models.TextField(
        blank=True,
        help_text="Strengths identified in response",
    )
    areas_for_improvement = models.TextField(
        blank=True,
        help_text="Areas needing improvement",
    )
    
    # Ensemble consensus
    evaluation_agreement_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Agreement level between evaluating LLMs (0-1)",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["response"]),
            models.Index(fields=["evaluator_model"]),
        ]

    def __str__(self):
        return f"Evaluation of Response #{self.response.id}"
