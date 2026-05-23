from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Basic user information serializer."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "is_verified"]
        read_only_fields = ["id", "is_verified"]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Password must be at least 8 characters",
    )
    password_confirm = serializers.CharField(
        write_only=True,
        help_text="Password confirmation",
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
            "role",
        ]

    def validate(self, data):
        """Validate password confirmation."""
        if data["password"] != data.pop("password_confirm"):
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        """Create new user with hashed password."""
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=validated_data.get("role", "student"),
            password=validated_data["password"],
        )
        return user


class LecturerTokenSerializer(TokenObtainPairSerializer):
    """JWT token serializer for lecturer login."""

    def validate(self, attrs):
        """Verify user role and return custom claims."""
        data = super().validate(attrs)
        
        # Add custom claims
        data["user_id"] = self.user.id
        data["username"] = self.user.username
        data["role"] = self.user.role
        
        # Verify role
        if self.user.role != "lecturer":
            raise serializers.ValidationError("Only lecturers can use this endpoint")
        
        return data


class TestSessionSerializer(serializers.Serializer):
    """Test serializer for API connectivity."""
    
    message = serializers.CharField()
    timestamp = serializers.DateTimeField()
