"""
API Views for Question endpoints.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.questions.models import Question
from apps.lectures.models import Session
from apps.questions.api.serializers import (
    QuestionListSerializer,
    QuestionDetailSerializer,
)
from common.responses import APIResponse
from common.pagination import StandardResultsSetPagination


class QuestionListView(APIView):
    """
    List all questions for a session.
    GET /api/sessions/<session_id>/questions/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        """Get questions for session."""
        session = get_object_or_404(Session, id=session_id)

        # Check permissions
        if request.user.role != "lecturer":
            if session not in request.user.sessions.all():
                return APIResponse.forbidden("Access denied to this session.")
        else:
            if session.lecturer.user != request.user:
                return APIResponse.forbidden("Access denied to this session.")

        questions = Question.objects.filter(session=session).order_by("order")
        paginator = StandardResultsSetPagination()
        paginated = paginator.paginate_queryset(questions, request)
        serializer = QuestionListSerializer(paginated, many=True)

        return Response(paginator.get_paginated_response(serializer.data))


class QuestionDetailView(APIView):
    """
    Get question details.
    GET /api/questions/<question_id>/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, question_id):
        """Get question details."""
        question = get_object_or_404(Question, id=question_id)

        # Check permissions
        session = question.session
        if request.user.role != "lecturer":
            if session not in request.user.sessions.all():
                return APIResponse.forbidden("Access denied to this question.")
        else:
            if session.lecturer.user != request.user:
                return APIResponse.forbidden("Access denied to this question.")

        serializer = QuestionDetailSerializer(question)
        return APIResponse.success(data=serializer.data)
