from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.lecturers.models import Lecturer
from apps.users.models import User


class Session(models.Model):
    """Lecture session model capturing lecture metadata and processing state."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("recording", "Recording"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    ]

    lecturer = models.ForeignKey(
        Lecturer,
        on_delete=models.CASCADE,
        related_name="sessions",
        help_text="Lecturer leading the session",
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=500, help_text="Lecture title/topic")
    description = models.TextField(blank=True)
    class_taught = models.CharField(max_length=255, blank=True, help_text="Class or course name")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        help_text="Current session status",
    )

    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(
        null=True, blank=True, help_text="Total session duration in seconds"
    )

    target_question_count = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text="Number of assessment questions to generate",
    )
    auto_question_mode = models.BooleanField(
        default=True,
        help_text="Automatically determine question count based on content",
    )

    teaching_effectiveness_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Teaching effectiveness score for this session (0-100)",
    )
    average_student_comprehension = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Average student comprehension score for this session",
    )
    teaching_scope_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Teaching scope coverage score for this session (0-100)",
    )

    tips = models.JSONField(
        default=dict,
        blank=True,
        help_text="Lecturing tips: topics to revisit, explanation tips, top 3 actions",
    )

    transcript_ready = models.BooleanField(
        default=False, help_text="Full transcript generated"
    )
    summary_ready = models.BooleanField(
        default=False, help_text="Summary processing complete"
    )
    questions_ready = models.BooleanField(
        default=False, help_text="Questions generated"
    )
    evaluation_ready = models.BooleanField(
        default=False, help_text="Student responses evaluated"
    )
    results_published = models.BooleanField(
        default=False, help_text="Results visible to student view"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["lecturer", "-started_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-started_at"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.lecturer.user.get_full_name()}"