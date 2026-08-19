"""
API Views for Session results and summaries.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from apps.lectures.models import Session
from common.responses import APIResponse


class SessionResultsView(APIView):
    """
    Get teaching effectiveness scores and tips for a session.
    GET /api/sessions/<session_id>/results/
    """

    permission_classes = [AllowAny]

    def get(self, request, session_id):
        session = get_object_or_404(Session, id=session_id)
        data = {
            "id": session.id,
            "title": session.title,
            "class_taught": session.class_taught,
            "status": session.status,
            "teaching_effectiveness_score": session.teaching_effectiveness_score,
            "average_student_comprehension": session.average_student_comprehension,
            "teaching_scope_score": session.teaching_scope_score,
            "tips": session.tips,
            "started_at": session.started_at,
            "ended_at": session.ended_at,
        }
        return APIResponse.success(data=data)
