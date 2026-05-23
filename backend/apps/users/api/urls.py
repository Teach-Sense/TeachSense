"""
URL routing for Authentication and User API.
"""
from django.urls import path
from apps.users.api.views import (
    LoginView,
    RegisterView,
    TokenObtainPairView,
    TokenRefreshView,
    ProfileView,
    ChangePasswordView,
    LogoutView,
)

app_name = "auth-api"

urlpatterns = [
    # Authentication
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("token/", TokenObtainPairView.as_view(), name="token-obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    
    # User profile
    path("profile/", ProfileView.as_view(), name="profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
]
