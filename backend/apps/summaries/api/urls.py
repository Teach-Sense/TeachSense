"""
URL routing for Summaries API.
"""
from django.urls import path
from apps.summaries.api.views import SessionResultsView

app_name = "summaries-api"

urlpatterns = [
    path("sessions/<int:session_id>/results/", SessionResultsView.as_view(), name="session-results"),
]
