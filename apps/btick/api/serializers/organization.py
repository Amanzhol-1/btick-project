from rest_framework import serializers

from apps.btick.models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    """
    Organization serializer
    """

    class Meta:
        model = Organization
        fields = ['id', 'name', 'website', 'contact_email', 'created_at']
        read_only_fields = ['id', 'created_at']


class OrganizationListSerializer(serializers.ModelSerializer):
    """
    Organization list serializer
    """

    class Meta:
        model = Organization
        fields = ['id', 'name']