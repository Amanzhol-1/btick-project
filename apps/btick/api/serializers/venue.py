from rest_framework import serializers

from apps.btick.models import Venue


class VenueSerializer(serializers.ModelSerializer):
    """
    Serializer for Venue model
    """

    class Meta:
        model = Venue
        fields = ['id', 'name', 'address', 'capacity', 'created_at']
        read_only_fields = ['id', 'created_at']


class VenueListSerializer(serializers.ModelSerializer):
    """
    Serializer for VenueList model
    """
    class Meta:
        model = Venue
        fields = ['id', 'name', 'address']