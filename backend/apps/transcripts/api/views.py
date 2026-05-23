"""
API Views for Transcript endpoints.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.transcripts.models import Transcript
from apps.lectures.models import Session
from apps.transcripts.api.serializers import (
    TranscriptListSerializer,
    TranscriptDetailSerializer,
    TranscriptCreateSerializer,
)
from common.responses import APIResponse
from common.pagination import StandardResultsSetPagination


class TranscriptUploadView(APIView):
    """
    Upload transcript for a session.
    POST /api/sessions/<session_id>/transcripts/
    GET /api/sessions/<session_id>/transcripts/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        """Get transcripts for session."""
        session = get_object_or_404(Session, id=session_id)

        # Check permissions
        if request.user.role != "lecturer":
            if session not in request.user.sessions.all():
                return APIResponse.forbidden("Access denied to this session.")
        else:
            if session.lecturer.user != request.user:
                return APIResponse.forbidden("Access denied to this session.")

        transcripts = Transcript.objects.filter(session=session)
        paginator = StandardResultsSetPagination()
        paginated = paginator.paginate_queryset(transcripts, request)
        serializer = TranscriptListSerializer(paginated, many=True)

        return Response(paginator.get_paginated_response(serializer.data))

    def post(self, request, session_id):
        """Upload new transcript."""
        session = get_object_or_404(Session, id=session_id)

        # Check lecturer permissions
        if request.user.role != "lecturer" or session.lecturer.user != request.user:
            return APIResponse.forbidden("Only the session lecturer can upload transcripts.")

        # Add session to data
        data = request.data.copy()
        data["session"] = session.id

        serializer = TranscriptCreateSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            transcript = serializer.save()
            return APIResponse.created(
                data=TranscriptDetailSerializer(transcript).data,
                message="Transcript uploaded successfully. Processing started.",
            )

        return APIResponse.validation_error(
            errors=serializer.errors,
            message="Failed to upload transcript.",
        )


class TranscriptDetailView(APIView):
    """
    Get transcript details.
    GET /api/transcripts/<id>/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, transcript_id):
        """Get transcript details."""
        transcript = get_object_or_404(Transcript, id=transcript_id)

        # Check permissions
        session = transcript.session
        if request.user.role != "lecturer":
            if session not in request.user.sessions.all():
                return APIResponse.forbidden("Access denied to this transcript.")
        else:
            if session.lecturer.user != request.user:
                return APIResponse.forbidden("Access denied to this transcript.")

        serializer = TranscriptDetailSerializer(transcript)
        return APIResponse.success(data=serializer.data)
