from rest_framework import serializers

from apps.btick.models import Event
from .category import EventCategorySerializer
from .venue import VenueListSerializer
from .organization import OrganizationListSerializer
from .ticket import TicketListSerializer


class EventListSerializer(serializers.ModelSerializer):
    """
    Serializer for Event listing (optimized for list views).
    """

    organization = OrganizationListSerializer(read_only=True)
    venue = VenueListSerializer(read_only=True)
    category = EventCategorySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'organization',
            'venue',
            'category',
            'starts_at',
            'ends_at',
            'status',
            'status_display',
        ]
        read_only_fields = ['id', 'status']


class EventDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for Event detail view (includes all information).
    """

    organization = OrganizationListSerializer(read_only=True)
    venue = VenueListSerializer(read_only=True)
    category = EventCategorySerializer(read_only=True)
    tickets = TicketListSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'description',
            'organization',
            'venue',
            'category',
            'tickets',
            'starts_at',
            'ends_at',
            'status',
            'status_display',
            'capacity',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']


class EventCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new events.
    """

    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'organization',
            'venue',
            'category',
            'starts_at',
            'ends_at',
            'capacity',
        ]

    def validate(self, attrs):
        """
        Validate event creation data.
        """
        from django.utils import timezone

        if attrs.get('starts_at') and attrs['starts_at'] < timezone.now():
            raise serializers.ValidationError({
                'starts_at': 'Event start time must be in the future.'
            })

        if attrs.get('ends_at') and attrs.get('starts_at'):
            if attrs['ends_at'] <= attrs['starts_at']:
                raise serializers.ValidationError({
                    'ends_at': 'Event end time must be after start time.'
                })

        return attrs