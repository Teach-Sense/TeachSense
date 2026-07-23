"""Analytics computation service."""

from __future__ import annotations

import logging
from statistics import mean

from apps.analytics.models import SessionAnalytics
from apps.lectures.models import Session
from apps.questions.models import Question
from apps.responses.models import Response


logger = logging.getLogger(__name__)


class AnalyticsService:
	"""Builds session-level analytics from questions, responses, and evaluations."""

	def compute_session_analytics(self, session_id: int) -> SessionAnalytics:
		session = Session.objects.get(id=session_id)
		questions = Question.objects.filter(session=session)
		responses = Response.objects.filter(question__session=session)

		evaluated = responses.filter(evaluation_status="evaluated")

		accuracy_scores = [response.accuracy_score for response in evaluated if response.accuracy_score is not None]
		completeness_scores = [response.completeness_score for response in evaluated if response.completeness_score is not None]
		clarity_scores = [response.clarity_score for response in evaluated if response.clarity_score is not None]
		overall_scores = [response.overall_score for response in evaluated if response.overall_score is not None]

		summary_confidence = None
		if hasattr(session, "summary") and session.summary:
			summary_confidence = (
				session.summary.model_agreement_score
				if session.summary.model_agreement_score is not None
				else session.summary.accuracy_score
			)

		engagement_score = 0.0
		if questions.exists():
			engagement_score = min(100.0, (responses.count() / max(questions.count(), 1)) * 100.0)

		analytics, _ = SessionAnalytics.objects.update_or_create(
			session=session,
			defaults={
				"total_questions": questions.count(),
				"evaluated_responses": evaluated.count(),
				"average_accuracy": mean(accuracy_scores) if accuracy_scores else None,
				"average_completeness": mean(completeness_scores) if completeness_scores else None,
				"average_clarity": mean(clarity_scores) if clarity_scores else None,
				"overall_effectiveness": (
					session.teaching_effectiveness_score
					if session.teaching_effectiveness_score is not None
					else (mean(overall_scores) if overall_scores else None)
				),
				"summary_confidence": summary_confidence,
				"engagement_score": engagement_score,
				"insights": self._build_insights(session, questions.count(), evaluated.count()),
			},
		)
		logger.info("Analytics refreshed for session %s", session_id)
		return analytics

	def _build_insights(self, session: Session, total_questions: int, evaluated_responses: int) -> list[str]:
		insights = []
		if session.summary_ready:
			insights.append("Lecture summary completed successfully.")
		if session.questions_ready:
			insights.append(f"{total_questions} questions were generated for the session.")
		if session.evaluation_ready:
			insights.append(f"{evaluated_responses} responses were evaluated.")
		if session.results_published:
			insights.append("Results were published to the student view.")
		return insights


def get_analytics_service() -> AnalyticsService:
	return AnalyticsService()
