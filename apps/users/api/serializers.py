"""
Serializers for Authentication and User API.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.models import User
from django.contrib.auth import authenticate


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""

    is_lecturer = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_lecturer",
            "is_active",
        )

    def get_is_lecturer(self, obj):
        return obj.role == "lecturer"


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    is_lecturer = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "role",
            "is_lecturer",
        )

    def validate(self, attrs):
        """Validate password match."""
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        """Create user with hashed password."""
        validated_data.pop("password_confirm")
        is_lecturer = validated_data.pop("is_lecturer", False)
        password = validated_data.pop("password")

        # Prefer explicit role when supplied, otherwise map the boolean helper.
        if is_lecturer:
            validated_data["role"] = "lecturer"
        elif not validated_data.get("role"):
            validated_data["role"] = "student"

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token obtain serializer with user info."""

    @classmethod
    def get_token(cls, user):
        """Override to add custom claims."""
        token = super().get_token(user)
        token["username"] = user.username
        token["email"] = user.email
        token["role"] = user.role
        token["is_lecturer"] = user.is_lecturer
        return token

    def validate(self, attrs):
        """Authenticate user."""
        username = attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise serializers.ValidationError("Username and password required.")

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")

        attrs["user"] = user
        return attrs


class LoginSerializer(serializers.Serializer):
    """Serializer for login endpoint."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate user."""
        username = attrs.get("username")
        password = attrs.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid username or password.")

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        """Generate tokens for user."""
        user = validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return {
            "user": UserSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        }


class TokenRefreshSerializer(TokenRefreshSerializer):
    """Token refresh serializer."""

    pass


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        """Validate passwords."""
        if attrs.get("new_password") != attrs.get("new_password_confirm"):
            raise serializers.ValidationError({"new_password": "Passwords do not match."})
        return attrs
