"""
URL routing for Responses API.
"""
from django.urls import path
from apps.responses.api.views import (
    ResponseListCreateView,
    ResponseDetailView,
    SessionResponsesView,
)

app_name = "responses-api"

urlpatterns = [
    # Responses
    path("sessions/<int:session_id>/questions/<int:question_id>/responses/", ResponseListCreateView.as_view(), name="response-list-create"),
    path("sessions/<int:session_id>/responses/", SessionResponsesView.as_view(), name="session-responses"),
    path("<int:response_id>/", ResponseDetailView.as_view(), name="response-detail"),
]
