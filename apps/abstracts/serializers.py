# Python modules
from typing import Any

# Django modules

# Django Rest Framework modules
from rest_framework import serializers

# Third-party modules

# Project modules
from apps.accounts.models import User


class UserForeignSerializer(serializers.ModelSerializer):
    """
    Serializer for representing users in foreign key relationships.

    Used when embedding user data in other serializers.
    """

    full_name = serializers.SerializerMethodField()

    class Meta:
        """Meta options for UserForeignSerializer."""

        model = User
        fields: tuple[str, ...] = ("id", "email", "full_name", "date_joined")
        read_only_fields: tuple[str, ...] = ("id", "email", "full_name", "date_joined")

    def get_full_name(self, obj: Any) -> str:
        """
        Get the user's full name.

        Returns:
            str: Full name if available, otherwise email.
        """
        return obj.get_full_name()
