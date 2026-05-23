from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.questions.models import Question


class Response(models.Model):
    """Student response to an assessment question."""

    EVALUATION_STATUS_CHOICES = [
        ("pending", "Pending Evaluation"),
        ("evaluated", "Evaluated"),
        ("skipped", "Skipped"),
    ]

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="responses",
        help_text="Question being responded to",
    )
    
    # Student identifier (can be anonymous in shared session)
    student_identifier = models.CharField(
        max_length=100,
        help_text="Unique identifier for student in session",
    )
    
    # Response content
    response_text = models.TextField(
        help_text="Student's verbal response (transcribed)",
    )
    audio_file = models.FileField(
        upload_to="uploads/responses/%Y/%m/%d/",
        null=True,
        blank=True,
        help_text="Audio recording of student response",
    )
    audio_duration_seconds = models.FloatField(
        null=True,
        blank=True,
        help_text="Duration of response audio",
    )
    
    # Evaluation results
    evaluation_status = models.CharField(
        max_length=20,
        choices=EVALUATION_STATUS_CHOICES,
        default="pending",
        help_text="Current evaluation status",
    )
    
    # Scoring
    accuracy_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Accuracy of response (0-100)",
    )
    completeness_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Completeness of response (0-100)",
    )
    clarity_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Clarity of expression (0-100)",
    )
    overall_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Overall response score (0-100)",
    )
    
    # Feedback
    feedback = models.TextField(
        blank=True,
        help_text="Evaluator feedback on response",
    )
    
    # Ensemble metrics
    ensemble_agreement_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="LLM ensemble agreement on evaluation (0-1)",
    )
    ensemble_confidence_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Ensemble confidence in evaluation (0-1)",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        unique_together = ["question", "student_identifier"]
        indexes = [
            models.Index(fields=["question", "student_identifier"]),
            models.Index(fields=["evaluation_status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"Response to Q{self.question.order} by {self.student_identifier}"
