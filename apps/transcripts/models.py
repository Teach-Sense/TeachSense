from django.db import models
from apps.lectures.models import Session


class Transcript(models.Model):
    """Full lecture transcript from speech-to-text processing."""

    session = models.OneToOneField(
        Session,
        on_delete=models.CASCADE,
        related_name="transcript",
        help_text="Session this transcript belongs to",
    )
    
    # Full transcript text
    full_text = models.TextField(
        help_text="Complete lecture transcript from STT service"
    )
    
    # Metadata
    total_words = models.IntegerField(default=0)
    language = models.CharField(max_length=10, default="en")
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Average STT confidence (0-1)",
    )
    
    # Processing state
    preprocessed = models.BooleanField(
        default=False, help_text="Data cleaned/validated"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["session"]),
        ]

    def __str__(self):
        return f"Transcript: {self.session.title}"
