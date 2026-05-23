"""
API Views for Authentication and User endpoints.
"""
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView as JWTTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView as JWTTokenRefreshView

from apps.users.models import User
from apps.users.api.serializers import (
    UserSerializer,
    UserCreateSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
)
from common.responses import APIResponse
from common.rate_limit import rate_limit


class LoginView(APIView):
    """
    Login endpoint with JWT token generation.
    POST /api/auth/login/
    Rate limited: 30 requests per minute per user/IP
    """

    permission_classes = [AllowAny]

    @rate_limit(requests_per_minute=lambda: int(os.environ.get('RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE', 30)))
    def post(self, request):
        """Authenticate user and return tokens."""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return APIResponse.success(
                data=result,
                message="Login successful.",
            )

        return APIResponse.validation_error(
            errors=serializer.errors,
            message="Login failed.",
        )


class RegisterView(APIView):
    """
    User registration endpoint.
    POST /api/auth/register/
    Rate limited: 30 requests per minute per user/IP
    """

    permission_classes = [AllowAny]

    @rate_limit(requests_per_minute=lambda: int(os.environ.get('RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE', 30)))
    def post(self, request):
        """Create new user account."""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate tokens for new user
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)

            return APIResponse.created(
                data={
                    "user": UserSerializer(user).data,
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                },
                message="Account created successfully.",
            )

        return APIResponse.validation_error(
            errors=serializer.errors,
            message="Registration failed.",
        )


class TokenObtainPairView(JWTTokenObtainPairView):
    """
    Override JWT token obtain view with custom serializer.
    POST /api/auth/token/
    """

    serializer_class = CustomTokenObtainPairSerializer


class TokenRefreshView(JWTTokenRefreshView):
    """
    Refresh JWT access token.
    POST /api/auth/token/refresh/
    """

    pass


class ProfileView(APIView):
    """
    Get or update user profile.
    GET /api/auth/profile/
    PUT /api/auth/profile/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user profile."""
        serializer = UserSerializer(request.user)
        return APIResponse.success(data=serializer.data)

    def put(self, request):
        """Update user profile."""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            return APIResponse.success(
                data=UserSerializer(user).data,
                message="Profile updated successfully.",
            )

        return APIResponse.validation_error(
            errors=serializer.errors,
            message="Failed to update profile.",
        )


class ChangePasswordView(APIView):
    """
    Change user password.
    POST /api/auth/change-password/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Change password."""
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user

            # Verify old password
            if not user.check_password(serializer.validated_data["old_password"]):
                return APIResponse.error(
                    message="Old password is incorrect.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Set new password
            user.set_password(serializer.validated_data["new_password"])
            user.save()

            return APIResponse.success(
                message="Password changed successfully.",
            )

        return APIResponse.validation_error(
            errors=serializer.errors,
            message="Failed to change password.",
        )


class LogoutView(APIView):
    """
    Logout endpoint (blacklist token on client).
    POST /api/auth/logout/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Logout user."""
        # Token is blacklisted on client side
        # This is a placeholder for future blacklist functionality
        return APIResponse.success(
            message="Logged out successfully.",
        )
