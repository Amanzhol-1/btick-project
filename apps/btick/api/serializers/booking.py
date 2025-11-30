from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.btick.models import Booking, EventsTicket, BookingStatus
from .ticket import TicketSerializer
from .event import EventListSerializer


class BookingListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing user bookings.
    """

    event_ticket = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'event_ticket',
            'quantity',
            'status',
            'status_display',
            'total_price',
            'expires_at',
            'created_at',
        ]
        read_only_fields = ['id', 'status', 'created_at']

    def get_total_price(self, obj):
        """
        Calculate total booking price.
        """
        return obj.event_ticket.price * obj.quantity

    def get_event_ticket(self, obj):
        """
        Get ticket information.
        """
        return TicketSerializer(obj.event_ticket).data


class BookingDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed booking view.
    """

    event = serializers.SerializerMethodField()
    event_ticket = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'event',
            'event_ticket',
            'quantity',
            'status',
            'status_display',
            'total_price',
            'expires_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

    def get_event(self, obj):
        """
        Get event information from ticket.
        """
        return EventListSerializer(obj.event_ticket.event).data

    def get_total_price(self, obj):
        """
        Calculate total booking price.
        """
        return obj.event_ticket.price * obj.quantity

    def get_event_ticket(self, obj):
        """
        Get ticket information.
        """
        return TicketSerializer(obj.event_ticket).data


class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new bookings.
    """

    class Meta:
        model = Booking
        fields = ['event_ticket', 'quantity']

    def validate_quantity(self, value):
        """
        Validate booking quantity.
        """
        if value < 1:
            raise serializers.ValidationError('Quantity must be at least 1.')
        if value > 10:
            raise serializers.ValidationError('Maximum 10 tickets per booking.')
        return value

    def validate(self, attrs):
        """
        Validate booking creation.
        """
        event_ticket = attrs['event_ticket']
        quantity = attrs['quantity']
        event = event_ticket.event

        if event.status != 'PUBLISHED':
            raise serializers.ValidationError({
                'event_ticket': 'This event is not available for booking.'
            })

        if event.starts_at <= timezone.now():
            raise serializers.ValidationError({
                'event_ticket': 'This event has already started.'
            })

        available = event_ticket.quota - event_ticket.sold
        if available < quantity:
            raise serializers.ValidationError({
                'quantity': f'Only {available} tickets available.'
            })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """
        Create booking and update ticket inventory.
        """
        event_ticket = validated_data['event_ticket']
        quantity = validated_data['quantity']
        user = self.context['request'].user

        ticket = EventsTicket.objects.select_for_update().get(pk=event_ticket.pk)

        available = ticket.quota - ticket.sold
        if available < quantity:
            raise serializers.ValidationError({
                'quantity': f'Only {available} tickets available.'
            })

        ticket.sold += quantity
        ticket.save(update_fields=['sold'])

        expires_at = timezone.now() + timezone.timedelta(minutes=15)

        booking = Booking.objects.create(
            user=user,
            event_ticket=ticket,
            quantity=quantity,
            status=BookingStatus.PENDING,
            expires_at=expires_at,
        )

        return booking


class BookingCancelSerializer(serializers.Serializer):
    """
    Serializer for cancelling bookings.
    """

    def validate(self, attrs):
        """
        Validate booking can be cancelled.
        """
        booking = self.instance

        if booking.status == BookingStatus.CANCELLED:
            raise serializers.ValidationError('Booking is already cancelled.')

        if booking.event_ticket.event.starts_at <= timezone.now():
            raise serializers.ValidationError('Cannot cancel booking for past events.')

        return attrs

    @transaction.atomic
    def save(self):
        """
        Cancel booking and return tickets to inventory.
        """
        booking = self.instance

        ticket = EventsTicket.objects.select_for_update().get(pk=booking.event_ticket.pk)

        ticket.sold -= booking.quantity
        ticket.save(update_fields=['sold'])

        booking.status = BookingStatus.CANCELLED
        booking.save(update_fields=['status'])

        return booking


class BookingConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming pending bookings.
    """

    def validate(self, attrs):
        """
        Validate booking can be confirmed.
        """
        booking = self.instance

        if booking.status != BookingStatus.PENDING:
            raise serializers.ValidationError('Only pending bookings can be confirmed.')

        if booking.expires_at and booking.expires_at <= timezone.now():
            raise serializers.ValidationError('Booking has expired.')

        return attrs

    def save(self):
        """
        Confirm the booking.
        """
        booking = self.instance
        booking.status = BookingStatus.CONFIRMED
        booking.expires_at = None
        booking.save(update_fields=['status', 'expires_at'])

        return booking