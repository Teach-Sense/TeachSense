"""
URL routing for Transcripts API.
"""
from django.urls import path
from apps.transcripts.api.views import (
    TranscriptUploadView,
    TranscriptDetailView,
)

app_name = "transcripts-api"

urlpatterns = [
    # Transcripts
    path("sessions/<int:session_id>/transcripts/", TranscriptUploadView.as_view(), name="transcript-upload"),
    path("<int:transcript_id>/", TranscriptDetailView.as_view(), name="transcript-detail"),
]
