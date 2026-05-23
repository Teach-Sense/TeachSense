from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.lectures.models import Session


class Question(models.Model):
    """Assessment question generated from lecture."""

    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="questions",
        help_text="Session this question belongs to",
    )
    
    # Question content
    question_text = models.TextField(
        help_text="The assessment question"
    )
    model_answer = models.TextField(
        help_text="Expected/model answer for this question"
    )
    
    # Question metadata
    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default="medium",
        help_text="Question difficulty",
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order of question in session",
    )
    
    # TTS audio
    audio_file = models.FileField(
        upload_to="uploads/questions/%Y/%m/%d/",
        null=True,
        blank=True,
        help_text="TTS audio file for this question",
    )
    audio_duration_seconds = models.FloatField(
        null=True,
        blank=True,
        help_text="Duration of audio recording",
    )
    
    # Quality metrics
    ensemble_agreement_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="LLM ensemble agreement on this question (0-1)",
    )
    ensemble_confidence_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Ensemble confidence in question quality (0-1)",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        indexes = [
            models.Index(fields=["session", "order"]),
            models.Index(fields=["difficulty_level"]),
        ]

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."
