"""Dashboard views for consolidated session status."""

from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.models import Session


class DashboardOverviewView(APIView):
	"""Return a compact overview of recent lecture sessions."""

	def get(self, request):
		sessions = Session.objects.select_related("lecturer", "summary", "transcript").order_by("-started_at")[:20]

		payload = []
		for session in sessions:
			analytics = getattr(session, "analytics", None)
			payload.append(
				{
					"id": session.id,
					"title": session.title,
					"status": session.status,
					"transcript_ready": session.transcript_ready,
					"summary_ready": session.summary_ready,
					"questions_ready": session.questions_ready,
					"evaluation_ready": session.evaluation_ready,
					"results_published": session.results_published,
					"teaching_effectiveness_score": session.teaching_effectiveness_score,
					"average_student_comprehension": session.average_student_comprehension,
					"analytics": None
					if analytics is None
					else {
						"total_questions": analytics.total_questions,
						"evaluated_responses": analytics.evaluated_responses,
						"average_accuracy": analytics.average_accuracy,
						"average_completeness": analytics.average_completeness,
						"average_clarity": analytics.average_clarity,
						"overall_effectiveness": analytics.overall_effectiveness,
						"engagement_score": analytics.engagement_score,
					},
					"started_at": session.started_at,
				}
			)

		return Response({"sessions": payload})
