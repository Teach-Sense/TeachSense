"""
URL routing for Questions API.
"""
from django.urls import path
from apps.questions.api.views import (
    QuestionListView,
    QuestionDetailView,
)

app_name = "questions-api"

urlpatterns = [
    # Questions
    path("sessions/<int:session_id>/questions/", QuestionListView.as_view(), name="question-list"),
    path("<int:question_id>/", QuestionDetailView.as_view(), name="question-detail"),
]
