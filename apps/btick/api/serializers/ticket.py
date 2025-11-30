from rest_framework import serializers

from apps.btick.models import EventsTicket


class TicketSerializer(serializers.ModelSerializer):
    """
    Serializer for Ticker
    """

    ticket_type_display = serializers.CharField(source='get_ticket_type_display', read_only=True)
    available = serializers.SerializerMethodField()

    class Meta:
        model = EventsTicket
        fields = [
            'id',
            'event',
            'ticket_type',
            'ticket_type_display',
            'price',
            'quota',
            'sold',
            'available',
            'created_at',
        ]
        read_only_fields = ['id', 'sold', 'created_at']

    def get_available(self, obj):
        """
        Calculate the number of available tickets
        """
        return obj.quota - obj.sold


class TicketListSerializer(serializers.ModelSerializer):
    """
    Serializer for TicketList
    """

    ticket_type_display = serializers.CharField(source='get_ticket_type_display', read_only=True)
    available = serializers.SerializerMethodField()

    class Meta:
        model = EventsTicket
        fields = [
            'id',
            'ticket_type',
            'ticket_type_display',
            'price',
            'available'
        ]

    def get_available(self, obj):
        """
        Calculate the number of available tickets
        """
        return obj.quota - obj.sold


