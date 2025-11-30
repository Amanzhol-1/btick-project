from rest_framework import serializers

from apps.accounts.models import User


class UserForeignSerializer(serializers.ModelSerializer):
    """
    Serializer for representing users in foreign key relationships.
    Used when embedding user data in other serializers.
    """
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'date_joined']
        read_only_fields = fields

    def get_full_name(self, obj):
        """
        Get the user's full name.

        Returns:
            str: Full name if available, otherwise email.
        """
        return obj.get_full_name()
