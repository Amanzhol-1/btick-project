from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.btick.models import (
    EventCategory,
    Venue,
    Organization,
    EventsTicket,
    Event,
    Booking,
    BookingStatus,
    EventStatus,
    OrganizationMembership,
    VenueMembership,
    OrganizationRole,
    VenueRole,
)
from apps.accounts.models import User


# =============================================================================
# Category Serializers
# =============================================================================

class EventCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for EventCategory model.
    """

    class Meta:
        model = EventCategory
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']


# =============================================================================
# Venue Serializers
# =============================================================================

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


# =============================================================================
# Organization Serializers
# =============================================================================

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


# =============================================================================
# Ticket Serializers
# =============================================================================

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


# =============================================================================
# Event Serializers
# =============================================================================

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


# =============================================================================
# Booking Serializers
# =============================================================================

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


# =============================================================================
# Management Serializers (for Organizers/Admins)
# =============================================================================

class EventManageSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating events by organizers.
    Validates that user has membership in the organization.
    """

    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'description',
            'organization',
            'venue',
            'category',
            'starts_at',
            'ends_at',
            'status',
            'capacity',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_organization(self, value):
        """
        Validate user has membership in the organization.
        """
        request = self.context.get('request')
        if request and request.user:
            user = request.user
            # Staff/superuser can manage any organization
            if user.is_staff or user.is_superuser:
                return value
            # Check membership
            if not OrganizationMembership.objects.filter(
                user=user,
                organization=value,
                role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER]
            ).exists():
                raise serializers.ValidationError(
                    "You must be an owner or manager of this organization."
                )
        return value

    def validate(self, attrs):
        """
        Validate event data.
        """
        starts_at = attrs.get('starts_at') or (self.instance.starts_at if self.instance else None)
        ends_at = attrs.get('ends_at') or (self.instance.ends_at if self.instance else None)

        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError({
                'ends_at': 'Event end time must be after start time.'
            })

        # For new events, start time must be in the future
        if not self.instance and starts_at and starts_at < timezone.now():
            raise serializers.ValidationError({
                'starts_at': 'Event start time must be in the future.'
            })

        return attrs


class EventPublishSerializer(serializers.Serializer):
    """
    Serializer for publishing a draft event.
    """

    def validate(self, attrs):
        """
        Validate event can be published.
        """
        event = self.instance

        if event.status == EventStatus.PUBLISHED:
            raise serializers.ValidationError('Event is already published.')

        if event.status == EventStatus.CANCELLED:
            raise serializers.ValidationError('Cannot publish a cancelled event.')

        if event.starts_at <= timezone.now():
            raise serializers.ValidationError('Cannot publish an event that has already started.')

        # Check if event has at least one ticket tier
        if not event.tickets.exists():
            raise serializers.ValidationError('Event must have at least one ticket tier before publishing.')

        return attrs

    def save(self):
        """
        Publish the event.
        """
        event = self.instance
        event.status = EventStatus.PUBLISHED
        event.save(update_fields=['status'])
        return event


class EventCancelEventSerializer(serializers.Serializer):
    """
    Serializer for cancelling an event.
    """

    def validate(self, attrs):
        """
        Validate event can be cancelled.
        """
        event = self.instance

        if event.status == EventStatus.CANCELLED:
            raise serializers.ValidationError('Event is already cancelled.')

        return attrs

    def save(self):
        """
        Cancel the event.
        """
        event = self.instance
        event.status = EventStatus.CANCELLED
        event.save(update_fields=['status'])
        return event


class TicketManageSerializer(serializers.ModelSerializer):
    """
    Serializer for managing ticket tiers by organizers.
    """
    available = serializers.SerializerMethodField(read_only=True)
    ticket_type_display = serializers.CharField(source='get_ticket_type_display', read_only=True)

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
        return obj.quota - obj.sold

    def validate_event(self, value):
        """
        Validate user can manage this event's tickets.
        """
        request = self.context.get('request')
        if request and request.user:
            user = request.user
            if user.is_staff or user.is_superuser:
                return value
            if not OrganizationMembership.objects.filter(
                user=user,
                organization=value.organization,
                role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER]
            ).exists():
                raise serializers.ValidationError(
                    "You must be an owner or manager of the event's organization."
                )
        return value

    def validate(self, attrs):
        """
        Validate ticket data.
        """
        event = attrs.get('event') or (self.instance.event if self.instance else None)

        # Check if event is not cancelled
        if event and event.status == EventStatus.CANCELLED:
            raise serializers.ValidationError("Cannot manage tickets for a cancelled event.")

        # For updates, ensure quota is not less than sold
        if self.instance:
            new_quota = attrs.get('quota', self.instance.quota)
            if new_quota < self.instance.sold:
                raise serializers.ValidationError({
                    'quota': f'Quota cannot be less than already sold tickets ({self.instance.sold}).'
                })

        return attrs


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for organization memberships.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = [
            'id',
            'user',
            'user_email',
            'user_name',
            'organization',
            'role',
            'role_display',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name()


class OrganizationMembershipCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for adding members to an organization.
    """
    user_email = serializers.EmailField(write_only=True)

    class Meta:
        model = OrganizationMembership
        fields = ['user_email', 'organization', 'role']

    def validate_user_email(self, value):
        """
        Validate user exists.
        """
        try:
            user = User.objects.get(email=value)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError(f"User with email '{value}' not found.")

    def validate(self, attrs):
        """
        Validate membership doesn't already exist.
        """
        user = attrs['user_email']  # This is now the User object
        organization = attrs['organization']

        if OrganizationMembership.objects.filter(user=user, organization=organization).exists():
            raise serializers.ValidationError("User is already a member of this organization.")

        return attrs

    def create(self, validated_data):
        """
        Create the membership.
        """
        user = validated_data.pop('user_email')  # This is the User object
        return OrganizationMembership.objects.create(user=user, **validated_data)


class VenueMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for venue memberships.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = VenueMembership
        fields = [
            'id',
            'user',
            'user_email',
            'user_name',
            'venue',
            'role',
            'role_display',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name()


class BookingAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for support staff to view/manage all bookings.
    Includes additional fields like user info.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    event = serializers.SerializerMethodField()
    event_ticket = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'user',
            'user_email',
            'user_name',
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
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name()

    def get_event(self, obj):
        return {
            'id': obj.event_ticket.event.id,
            'title': obj.event_ticket.event.title,
            'organization': obj.event_ticket.event.organization.name,
            'starts_at': obj.event_ticket.event.starts_at,
        }

    def get_event_ticket(self, obj):
        return {
            'id': obj.event_ticket.id,
            'ticket_type': obj.event_ticket.get_ticket_type_display(),
            'price': obj.event_ticket.price,
        }

    def get_total_price(self, obj):
        return obj.event_ticket.price * obj.quantity


class BookingRefundSerializer(serializers.Serializer):
    """
    Serializer for refunding bookings (support staff only).
    """

    def validate(self, attrs):
        """
        Validate booking can be refunded.
        """
        booking = self.instance

        if booking.status == BookingStatus.CANCELLED:
            raise serializers.ValidationError('Booking is already cancelled/refunded.')

        return attrs

    @transaction.atomic
    def save(self):
        """
        Refund the booking and return tickets to inventory.
        """
        booking = self.instance

        # Only return tickets if booking was confirmed
        if booking.status == BookingStatus.CONFIRMED:
            ticket = EventsTicket.objects.select_for_update().get(pk=booking.event_ticket.pk)
            ticket.sold -= booking.quantity
            ticket.save(update_fields=['sold'])

        booking.status = BookingStatus.CANCELLED
        booking.save(update_fields=['status'])

        return booking
