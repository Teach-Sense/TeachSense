from django.db import models

from apps.lectures.models import Session


class SessionAnalytics(models.Model):
	"""Aggregated analytics for a completed lecture session."""

	session = models.OneToOneField(
		Session,
		on_delete=models.CASCADE,
		related_name="analytics",
	)
	total_questions = models.IntegerField(default=0)
	evaluated_responses = models.IntegerField(default=0)
	average_accuracy = models.FloatField(null=True, blank=True)
	average_completeness = models.FloatField(null=True, blank=True)
	average_clarity = models.FloatField(null=True, blank=True)
	overall_effectiveness = models.FloatField(null=True, blank=True)
	summary_confidence = models.FloatField(null=True, blank=True)
	engagement_score = models.FloatField(null=True, blank=True)
	insights = models.JSONField(default=list, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-updated_at"]

	def __str__(self):
		return f"Analytics for {self.session.title}"
