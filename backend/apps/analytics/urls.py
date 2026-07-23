from django.urls import include, path


urlpatterns = [
	path("api/", include("apps.analytics.api.urls")),
]
