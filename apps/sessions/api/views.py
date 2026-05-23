"""
API Views for Session endpoints.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.lectures.models import Session
from apps.sessions.api.serializers import (
    SessionListSerializer,
    SessionDetailSerializer,
    SessionCreateSerializer,
    SessionUpdateSerializer,
)
from common.responses import APIResponse
from common.pagination import StandardResultsSetPagination
from common.permissions import IsLecturer, IsSessionOwner


class SessionListCreateView(APIView):
    """
    List all sessions for authenticated user or create new session.
    GET /api/sessions/
    POST /api/sessions/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List sessions for lecturers or enrolled sessions for students."""
        if request.user.role == "lecturer":
            sessions = Session.objects.filter(lecturer__user=request.user)
        else:
            lecturer_profile = getattr(request.user, "lecturer_profile", None)
            sessions = lecturer_profile.sessions.all() if lecturer_profile else Session.objects.none()

        paginator = StandardResultsSetPagination()
        paginated_sessions = paginator.paginate_queryset(sessions, request)
        serializer = SessionListSerializer(paginated_sessions, many=True)

        return Response(paginator.get_paginated_response(serializer.data))

    def post(self, request):
        """Create new session (lecturers only)."""
        if request.user.role != "lecturer":
            return APIResponse.forbidden("Only lecturers can create sessions.")

        serializer = SessionCreateSerializer(data=request.data)
        if serializer.is_valid():
            session = serializer.save()
            return APIResponse.created(
                data=SessionDetailSerializer(session).data,
                message="Session created successfully.",
            )

        return APIResponse.validation_error(
            errors=serializer.errors,
            message="Failed to create session.",
        )


class SessionDetailView(APIView):
    """
    Retrieve or update a specific session.
    GET /api/sessions/<id>/
    PUT /api/sessions/<id>/
    DELETE /api/sessions/<id>/
    """

    permission_classes = [IsAuthenticated]

    def get_session(self, session_id, request):
        """Get session and check permissions."""
        session = get_object_or_404(Session, id=session_id)
        
        # Check permissions
        if request.user.role != "lecturer":
            lecturer_profile = getattr(request.user, "lecturer_profile", None)
            if not lecturer_profile or session not in lecturer_profile.sessions.all():
                return None
        else:
            if session.lecturer.user != request.user:
                return None

        return session

    def get(self, request, session_id):
        """Get session details."""
        session = self.get_session(session_id, request)
        if not session:
            return APIResponse.forbidden("Access denied to this session.")

        serializer = SessionDetailSerializer(session)
        return APIResponse.success(data=serializer.data)

    def put(self, request, session_id):
        """Update session (lecturers only)."""
        session = self.get_session(session_id, request)
        if not session:
            return APIResponse.forbidden("Access denied to this session.")

        if request.user.role != "lecturer":
            return APIResponse.forbidden("Only lecturers can update sessions.")

        serializer = SessionUpdateSerializer(session, data=request.data, partial=True)
        if serializer.is_valid():
            updated_session = serializer.save()
            return APIResponse.success(
                data=SessionDetailSerializer(updated_session).data,
                message="Session updated successfully.",
            )

        return APIResponse.validation_error(
            errors=serializer.errors,
            message="Failed to update session.",
        )

    def delete(self, request, session_id):
        """Delete session (lecturers only)."""
        session = self.get_session(session_id, request)
        if not session:
            return APIResponse.forbidden("Access denied to this session.")

        if request.user.role != "lecturer":
            return APIResponse.forbidden("Only lecturers can delete sessions.")

        session.delete()
        return APIResponse.no_content(message="Session deleted successfully.")
