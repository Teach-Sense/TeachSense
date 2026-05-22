from django.urls import path

from apps.analytics.api.views import SessionAnalyticsView


urlpatterns = [
	path("sessions/<int:session_id>/", SessionAnalyticsView.as_view(), name="session-analytics"),
]
