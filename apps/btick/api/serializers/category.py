from rest_framework import serializers

from apps.btick.models import EventCategory


class EventCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for EventCategory model.
    """

    class Meta:
        model = EventCategory
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']