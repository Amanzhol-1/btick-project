# Python modules
from typing import Any

# Django modules
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

# Django Rest Framework modules
from rest_framework import serializers

# Third-party modules
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# Project modules


User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        """Meta options for UserRegistrationSerializer."""

        model = User
        fields: tuple[str, ...] = (
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone",
        )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate passwords match."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({
                "password_confirm": "Passwords don't match.",
            })
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Any:
        """Create and return a new user."""
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer that includes user info in response."""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate credentials and return tokens with user info."""
        data: dict[str, Any] = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for viewing and updating user profile."""

    class Meta:
        """Meta options for UserProfileSerializer."""

        model = User
        fields: tuple[str, ...] = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "bio",
            "avatar",
            "date_joined",
            "last_login",
        )
        read_only_fields: tuple[str, ...] = ("id", "email", "date_joined", "last_login")


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""

    old_password = serializers.CharField(
        required=True,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={"input_type": "password"},
    )

    def validate_old_password(self, value: str) -> str:
        """Validate current password is correct."""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate new passwords match."""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({
                "new_password_confirm": "New passwords don't match.",
            })
        return attrs

    def save(self, **kwargs: Any) -> Any:
        """Update user password."""
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user
