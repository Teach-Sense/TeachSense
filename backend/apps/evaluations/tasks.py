"""Celery tasks for response evaluation."""

import asyncio
import json
import logging

from celery import shared_task
from django.db import transaction

from apps.evaluations.models import Evaluation
from apps.analytics.tasks import refresh_session_analytics
from apps.lectures.models import Session
from apps.responses.models import Response
from apps.lectures.tasks import compute_teaching_effectiveness, publish_results_to_student_view
from apps.integrations.llm.ensemble import LLMEnsemble, EnsembleConfig, MergeStrategy


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def evaluate_session_responses(self, session_id: int):
	"""Evaluate all responses that belong to a lecture session."""
	try:
		session = Session.objects.get(id=session_id)
		responses = (
			Response.objects.select_related("question")
			.filter(question__session=session)
			.order_by("question__order", "created_at")
		)

		if not responses.exists():
			session.evaluation_ready = True
			session.save(update_fields=["evaluation_ready"])
			return {"session_id": session_id, "evaluated": 0, "success": True}

		ensemble = LLMEnsemble(
			config=EnsembleConfig(
			primary_models=["claude-3-sonnet", "mistral-medium"],
			fallback_models=["mistral-small"],
			providers={},
		)

		evaluated_count = 0
		with transaction.atomic():
			for response in responses:
				shared_result = asyncio.run(
					ensemble.evaluate_student_response(
						question=response.question.question_text,
						student_answer=response.response_text,
						model_answer=response.question.model_answer,
					)
				)

				try:
					payload = json.loads(shared_result.merged_response)
				except json.JSONDecodeError:
					payload = {"score": 0, "feedback": shared_result.merged_response}

				score = float(payload.get("score", payload.get("accuracy", 0.0)) or 0.0)
				feedback = payload.get("feedback", "")
				accuracy = float(payload.get("accuracy", score) or score)
				completeness = float(payload.get("completeness", max(0.0, score - 8.0)) or 0.0)
				clarity = float(payload.get("clarity", min(100.0, score + 2.0)) or 0.0)

				Evaluation.objects.update_or_create(
					response=response,
					defaults={
						"evaluator_model": "multi-llm-ensemble",
						"accuracy_assessment": feedback or "Automated evaluation completed.",
						"completeness_assessment": f"Completeness score: {completeness:.1f}",
						"clarity_assessment": f"Clarity score: {clarity:.1f}",
						"strengths": "",
						"areas_for_improvement": "",
						"evaluation_agreement_score": shared_result.agreement_score,
					},
				)

				response.evaluation_status = "evaluated"
				response.accuracy_score = accuracy
				response.completeness_score = completeness
				response.clarity_score = clarity
				response.overall_score = score
				response.feedback = feedback
				response.ensemble_agreement_score = shared_result.agreement_score
				response.ensemble_confidence_score = shared_result.confidence_score
				response.save(
					update_fields=[
						"evaluation_status",
						"accuracy_score",
						"completeness_score",
						"clarity_score",
						"overall_score",
						"feedback",
						"ensemble_agreement_score",
						"ensemble_confidence_score",
					]
				)
				evaluated_count += 1

			session.evaluation_ready = True
			session.save(update_fields=["evaluation_ready"])

		compute_teaching_effectiveness.delay(session_id)
		publish_results_to_student_view.delay(session_id)
		refresh_session_analytics.delay(session_id)

		return {"session_id": session_id, "evaluated": evaluated_count, "success": True}

	except Exception as exc:
		logger.exception(f"Error evaluating responses for session {session_id}")
		raise self.retry(exc=exc, countdown=30)
