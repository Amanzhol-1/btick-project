# Python modules
from typing import Any

# Django Rest Framework modules
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

# Third-party modules
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, extend_schema_view

# Project modules
from apps.accounts.serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)


@extend_schema_view(
    register=extend_schema(tags=["Auth"], summary="Register a new user"),
    login=extend_schema(tags=["Auth"], summary="Login and obtain JWT tokens"),
    logout=extend_schema(tags=["Auth"], summary="Logout and blacklist refresh token"),
    profile=extend_schema(tags=["Auth"], summary="View or update user profile"),
    change_password=extend_schema(tags=["Auth"], summary="Change user password"),
)
class AccountViewSet(ViewSet):
    """
    ViewSet for account operations.

    Provides endpoints for user registration, authentication, and profile management.
    """

    def get_permissions(self) -> list:
        """Return permissions based on action."""
        if self.action in ["register", "login"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(methods=["POST"], detail=False, url_path="register")
    def register(self, request: Request) -> Response:
        """User registration endpoint."""
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        user = serializer.save()

        # Generate tokens for the new user
        refresh: RefreshToken = RefreshToken.for_user(user)

        return Response(
            status=status.HTTP_201_CREATED,
            data={
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
        )

    @action(methods=["POST"], detail=False, url_path="login")
    def login(self, request: Request) -> Response:
        """User login endpoint with JWT tokens."""
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.validated_data,
        )

    @action(methods=["POST"], detail=False, url_path="logout")
    def logout(self, request: Request) -> Response:
        """User logout endpoint - blacklists the refresh token."""
        refresh_token: str | None = request.data.get("refresh")
        if not refresh_token:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"error": "Refresh token is required."},
            )
        try:
            token: RefreshToken = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                status=status.HTTP_200_OK,
                data={"message": "Successfully logged out."},
            )
        except TokenError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"error": "Invalid token."},
            )

    @action(methods=["GET", "PATCH"], detail=False, url_path="profile")
    def profile(self, request: Request) -> Response:
        """User profile view and update endpoint."""
        user = request.user

        if request.method == "GET":
            serializer = UserProfileSerializer(user)
            return Response(
                status=status.HTTP_200_OK,
                data=serializer.data,
            )

        # PATCH request
        serializer = UserProfileSerializer(
            user,
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        serializer.save()
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    @action(methods=["POST"], detail=False, url_path="change-password")
    def change_password(self, request: Request) -> Response:
        """Change password endpoint."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        serializer.save()
        return Response(
            status=status.HTTP_200_OK,
            data={"message": "Password changed successfully."},
        )
