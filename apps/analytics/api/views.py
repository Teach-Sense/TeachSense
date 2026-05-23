"""API views for analytics reporting."""

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from apps.analytics.services.service import get_analytics_service


class SessionAnalyticsView(APIView):
	"""Return analytics for a single session."""

	def get(self, request, session_id: int):
		analytics = get_analytics_service().compute_session_analytics(session_id)

		return Response(
			{
				"session_id": session_id,
				"total_questions": analytics.total_questions,
				"evaluated_responses": analytics.evaluated_responses,
				"average_accuracy": analytics.average_accuracy,
				"average_completeness": analytics.average_completeness,
				"average_clarity": analytics.average_clarity,
				"overall_effectiveness": analytics.overall_effectiveness,
				"summary_confidence": analytics.summary_confidence,
				"engagement_score": analytics.engagement_score,
				"insights": analytics.insights,
			},
			status=status.HTTP_200_OK,
		)
