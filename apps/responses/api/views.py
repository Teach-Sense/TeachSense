"""
API Views for Response endpoints.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.responses.models import Response as ResponseModel
from apps.questions.models import Question
from apps.lectures.models import Session
from apps.responses.api.serializers import (
    ResponseListSerializer,
    ResponseDetailSerializer,
    ResponseCreateSerializer,
    ResponseUpdateSerializer,
)
from common.responses import APIResponse
from common.pagination import StandardResultsSetPagination


class ResponseListCreateView(APIView):
    """
    List responses for a question or create new response.
    GET /api/sessions/<session_id>/questions/<question_id>/responses/
    POST /api/sessions/<session_id>/questions/<question_id>/responses/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, session_id, question_id):
        """Get responses for question."""
        session = get_object_or_404(Session, id=session_id)
        question = get_object_or_404(Question, id=question_id, session=session)

        # Check permissions
        if request.user.role == "lecturer":
            if session.lecturer.user != request.user:
                return APIResponse.forbidden("Access denied to this session.")
        else:
            if session not in request.user.sessions.all():
                return APIResponse.forbidden("Access denied to this session.")

        responses = ResponseModel.objects.filter(question=question)
        
        # Students can only see their own responses
        if request.user.role != "lecturer":
            responses = responses.filter(student=request.user)

        paginator = StandardResultsSetPagination()
        paginated = paginator.paginate_queryset(responses, request)
        serializer = ResponseListSerializer(paginated, many=True)

        return Response(paginator.get_paginated_response(serializer.data))

    def post(self, request, session_id, question_id):
        """Create new response (students only)."""
        if request.user.role == "lecturer":
            return APIResponse.forbidden("Students can submit responses, not lecturers.")

        session = get_object_or_404(Session, id=session_id)
        question = get_object_or_404(Question, id=question_id, session=session)

        # Check student is enrolled
        if session not in request.user.sessions.all():
            return APIResponse.forbidden("You are not enrolled in this session.")

        # Check if already responded
        if ResponseModel.objects.filter(question=question, student=request.user).exists():
            return APIResponse.conflict("You have already submitted a response to this question.")

        data = request.data.copy()
        data["question"] = question.id

        serializer = ResponseCreateSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            response = serializer.save()
            return APIResponse.created(
                data=ResponseDetailSerializer(response).data,
                message="Response submitted successfully.",
            )

        return APIResponse.validation_error(
            errors=serializer.errors,
            message="Failed to submit response.",
        )


class ResponseDetailView(APIView):
    """
    Get or update response details.
    GET /api/responses/<response_id>/
    PUT /api/responses/<response_id>/
    DELETE /api/responses/<response_id>/
    """

    permission_classes = [IsAuthenticated]

    def get_response(self, response_id, request):
        """Get response and check permissions."""
        response = get_object_or_404(ResponseModel, id=response_id)

        # Check permissions
        if request.user.role == "lecturer":
            if response.question.session.lecturer.user != request.user:
                return None
        else:
            if response.student != request.user:
                return None

        return response

    def get(self, request, response_id):
        """Get response details."""
        response = self.get_response(response_id, request)
        if not response:
            return APIResponse.forbidden("Access denied to this response.")

        serializer = ResponseDetailSerializer(response)
        return APIResponse.success(data=serializer.data)

    def put(self, request, response_id):
        """Update response (students can update own responses)."""
        response = self.get_response(response_id, request)
        if not response:
            return APIResponse.forbidden("Access denied to this response.")

        if request.user.role == "lecturer":
            return APIResponse.forbidden("Only the student who submitted can update.")

        # Cannot update if already evaluated
        if response.evaluation_status == "evaluated":
            return APIResponse.conflict("Cannot update an already evaluated response.")

        serializer = ResponseUpdateSerializer(response, data=request.data, partial=True)
        if serializer.is_valid():
            updated_response = serializer.save()
            return APIResponse.success(
                data=ResponseDetailSerializer(updated_response).data,
                message="Response updated successfully.",
            )

        return APIResponse.validation_error(
            errors=serializer.errors,
            message="Failed to update response.",
        )

    def delete(self, request, response_id):
        """Delete response (students can delete own, lecturers admin only)."""
        response = self.get_response(response_id, request)
        if not response:
            return APIResponse.forbidden("Access denied to this response.")

        if request.user.role != "lecturer":
            if response.student != request.user:
                return APIResponse.forbidden("Only the student who submitted can delete.")

        response.delete()
        return APIResponse.no_content(message="Response deleted successfully.")


class SessionResponsesView(APIView):
    """
    List all responses for a session.
    GET /api/sessions/<session_id>/responses/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        """Get all responses for session."""
        session = get_object_or_404(Session, id=session_id)

        # Check lecturer permissions
        if request.user.role != "lecturer" or session.lecturer.user != request.user:
            return APIResponse.forbidden("Only the session lecturer can view all responses.")

        responses = ResponseModel.objects.filter(question__session=session)

        paginator = StandardResultsSetPagination()
        paginated = paginator.paginate_queryset(responses, request)
        serializer = ResponseListSerializer(paginated, many=True)

        return Response(paginator.get_paginated_response(serializer.data))
