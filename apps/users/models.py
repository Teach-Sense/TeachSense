from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model for TeachSense system."""

    ROLE_CHOICES = [
        ("lecturer", "Lecturer"),
        ("student", "Student"),
        ("admin", "Admin"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="student",
        help_text="User role in TeachSense system",
    )
    is_verified = models.BooleanField(
        default=False, help_text="Email verification status"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["is_verified"]),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    @property
    def is_lecturer(self):
        """Compatibility helper for existing code paths and API responses."""
        return self.role == "lecturer"

    @is_lecturer.setter
    def is_lecturer(self, value):
        """Allow boolean assignment to map onto the role field."""
        self.role = "lecturer" if value else "student"

    @property
    def is_student(self):
        return self.role == "student"
