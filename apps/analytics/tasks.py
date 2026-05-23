"""Background tasks for analytics generation."""

import logging

from celery import shared_task

from apps.analytics.services.service import get_analytics_service


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def refresh_session_analytics(self, session_id: int):
	"""Compute and persist analytics for a completed lecture session."""
	try:
		analytics = get_analytics_service().compute_session_analytics(session_id)
		return {
			"session_id": session_id,
			"analytics_id": analytics.id,
			"success": True,
		}
	except Exception as exc:
		logger.exception("Failed to refresh analytics for session %s", session_id)
		raise self.retry(exc=exc, countdown=30)
