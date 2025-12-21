# Python modules
from typing import Any

# Django modules
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError

# Django Rest Framework modules

# Third-party modules

# Project modules


class UserManager(BaseUserManager):
    """
    Custom manager for User model with email as the unique identifier.

    Provides methods for creating regular users and superusers.
    """

    def __obtain_user_instance(
        self,
        email: str,
        password: str | None,
        **extra_fields: Any,
    ) -> "User":
        """
        Private helper method to create and configure a User instance.

        Args:
            email: The user's email address.
            password: The user's password (optional).
            **extra_fields: Additional fields to set on the user.

        Returns:
            A configured but unsaved User instance.

        Raises:
            ValidationError: If email is not provided.
        """
        if not email:
            raise ValidationError(
                message="The Email field must be set.",
                code="email_required",
            )

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        return user

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """
        Create and save a regular user with the given email and password.

        Args:
            email: The user's email address.
            password: The user's password (optional).
            **extra_fields: Additional fields to set on the user.

        Returns:
            The created User instance.
        """
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user: "User" = self.__obtain_user_instance(email, password, **extra_fields)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """
        Create and save a superuser with the given email and password.

        Args:
            email: The user's email address.
            password: The user's password (optional).
            **extra_fields: Additional fields to set on the user.

        Returns:
            The created superuser User instance.

        Raises:
            ValidationError: If is_staff or is_superuser is not True.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValidationError(
                message="Superuser must have is_staff=True.",
                code="superuser_not_staff",
            )
        if extra_fields.get("is_superuser") is not True:
            raise ValidationError(
                message="Superuser must have is_superuser=True.",
                code="superuser_not_superuser",
            )

        user: "User" = self.__obtain_user_instance(email, password, **extra_fields)
        user.save(using=self._db)
        return user
