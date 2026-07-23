from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
	# Root redirect
	path("", RedirectView.as_view(url="docs/", permanent=False), name="root"),
	
	# Admin
	path("admin/", admin.site.urls),
	
	# API Documentation
	path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
	path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
	path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

	# Health / status
	path("api/health/", include("apps.core.api.urls")),
	
	# Authentication & Users
	path("api/auth/", include("apps.users.api.urls")),
	
	# Sessions (Lectures)
	path("api/sessions/", include("apps.sessions.api.urls")),
	
	# Transcripts
	path("api/transcripts/", include("apps.transcripts.api.urls")),
	
	# Questions
	path("api/questions/", include("apps.questions.api.urls")),
	
	# Responses
	path("api/responses/", include("apps.responses.api.urls")),
	
	# Devices
	path("api/devices/", include("apps.devices.api.urls")),
	
	# Analytics
	path("api/analytics/", include("apps.analytics.urls")),
	
	# Dashboards
	path("api/dashboards/", include("apps.dashboards.urls")),
]
