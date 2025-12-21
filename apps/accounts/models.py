# Python modules

# Django modules
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

# Django Rest Framework modules

# Third-party modules

# Project modules
from apps.accounts.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with email as the primary identifier.

    Extends AbstractBaseUser for full control over authentication fields.
    Includes PermissionsMixin for Django's permission framework support.
    """

    # Class constants for field lengths
    FIRST_NAME_MAX_LENGTH: int = 150
    LAST_NAME_MAX_LENGTH: int = 150
    PHONE_MAX_LENGTH: int = 20

    email = models.EmailField(
        unique=True,
        verbose_name="Email address",
        help_text="Unique email address used for authentication",
        error_messages={
            "unique": "A user with that email already exists.",
        },
    )

    # Name fields
    first_name = models.CharField(
        max_length=FIRST_NAME_MAX_LENGTH,
        blank=True,
        verbose_name="First name",
        help_text="User's first name",
    )
    last_name = models.CharField(
        max_length=LAST_NAME_MAX_LENGTH,
        blank=True,
        verbose_name="Last name",
        help_text="User's last name",
    )

    # Profile fields
    phone = models.CharField(
        max_length=PHONE_MAX_LENGTH,
        blank=True,
        verbose_name="Phone number",
        help_text="Optional phone number for contact",
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name="Avatar",
        help_text="Optional profile picture",
    )
    bio = models.TextField(
        blank=True,
        verbose_name="Biography",
        help_text="Optional user biography or description",
    )

    # Standard fields
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active",
        help_text="Designates whether this user should be treated as active. "
        "Unselect this instead of deleting accounts.",
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Staff status",
        help_text="Designates whether the user can log into this admin site.",
    )
    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date joined",
        help_text="Date and time when the user account was created",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        """Meta options for User model."""

        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        """String representation."""
        return self.email

    def __repr__(self) -> str:
        """Developer representation."""
        return f"User(id={self.pk}, email={self.email})"

    def get_full_name(self) -> str:
        """Return the first_name plus the last_name, with a space in between."""
        full_name: str = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def get_short_name(self) -> str:
        """Return the first name."""
        return self.first_name or self.email
