"""
API Views for Session endpoints.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
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


class SessionListCreateView(APIView):
    """
    List all sessions or create new session.
    GET /api/sessions/
    POST /api/sessions/
    """

    permission_classes = [AllowAny]

    def get(self, request):
        sessions = Session.objects.all().order_by("-started_at")
        paginator = StandardResultsSetPagination()
        paginated_sessions = paginator.paginate_queryset(sessions, request)
        serializer = SessionListSerializer(paginated_sessions, many=True)
        return Response(paginator.get_paginated_response(serializer.data))

    def post(self, request):
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

    permission_classes = [AllowAny]

    def get(self, request, session_id):
        session = get_object_or_404(Session, id=session_id)
        serializer = SessionDetailSerializer(session)
        return APIResponse.success(data=serializer.data)

    def put(self, request, session_id):
        session = get_object_or_404(Session, id=session_id)
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
        session = get_object_or_404(Session, id=session_id)
        session.delete()
        return APIResponse.no_content(message="Session deleted successfully.")