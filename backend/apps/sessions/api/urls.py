"""
URL routing for Sessions API.
"""
from django.urls import path
from apps.sessions.api.views import (
    SessionListCreateView,
    SessionDetailView,
)

app_name = "sessions-api"

urlpatterns = [
    # Sessions
    path("", SessionListCreateView.as_view(), name="session-list-create"),
    path("<int:session_id>/", SessionDetailView.as_view(), name="session-detail"),
]
