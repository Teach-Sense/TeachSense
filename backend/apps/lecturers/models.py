from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.users.models import User


class Lecturer(models.Model):
    """Lecturer profile with teaching effectiveness metrics."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="lecturer_profile",
        limit_choices_to={"role": "lecturer"},
    )
    
    # Teaching effectiveness metrics
    overall_effectiveness_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Aggregate teaching effectiveness score (0-100)",
    )
    total_sessions = models.IntegerField(default=0, help_text="Total lecture sessions")
    average_student_comprehension = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Average student comprehension across all sessions",
    )
    
    # Contact & bio
    bio = models.TextField(blank=True, help_text="Lecturer bio/about")
    department = models.CharField(max_length=255, blank=True)
    office_hours = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-overall_effectiveness_score"]
        indexes = [
            models.Index(fields=["-overall_effectiveness_score"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"Lecturer: {self.user.get_full_name()}"
