from django.db import models
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse

from apps.btick.models import (
    EventCategory,
    Venue,
    Organization,
    Event,
    EventsTicket,
    Booking,
    BookingStatus,
    OrganizationMembership,
    VenueMembership,
    OrganizationRole,
)
from apps.btick.serializers import (
    EventCategorySerializer,
    VenueSerializer,
    OrganizationSerializer,
    EventListSerializer,
    EventDetailSerializer,
    TicketListSerializer,
    TicketManageSerializer,
    BookingListSerializer,
    BookingDetailSerializer,
    BookingCreateSerializer,
    BookingCancelSerializer,
    BookingConfirmSerializer,
    EventManageSerializer,
    EventPublishSerializer,
    EventCancelEventSerializer,
    BookingAdminSerializer,
    BookingRefundSerializer,
    OrganizationMembershipSerializer,
    OrganizationMembershipCreateSerializer,
    VenueMembershipSerializer,
)
from apps.btick.filters import EventFilter
from apps.btick.permissions import (
    IsOrganizerOrAdmin,
    IsCustomer,
    IsSupportOrAdmin,
    CanManageEvent,
    CanPublishEvent,
    IsOrganizationMember,
    IsOrganizationOwnerOrManager,
    IsVenueMember,
    IsVenueManager,
    CanRefundBooking,
    IsAdminOrReadOnly,
)


# =============================================================================
# Category ViewSet
# =============================================================================

@extend_schema_view(
    list=extend_schema(tags=['Categories'], summary='List all event categories'),
    retrieve=extend_schema(tags=['Categories'], summary='Get category details'),
    create=extend_schema(tags=['Categories'], summary='Create category (Admin only)'),
    update=extend_schema(tags=['Categories'], summary='Update category (Admin only)'),
    partial_update=extend_schema(tags=['Categories'], summary='Partial update category (Admin only)'),
    destroy=extend_schema(tags=['Categories'], summary='Delete category (Admin only)'),
)
class EventCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EventCategory model

    Provides read-only access to event categories for all users.
    Only admins can create/update/delete categories.
    """

    queryset = EventCategory.objects.filter(is_active=True).order_by('name')
    serializer_class = EventCategorySerializer
    permission_classes = [IsAdminOrReadOnly]


# =============================================================================
# Venue ViewSet
# =============================================================================

@extend_schema_view(
    list=extend_schema(tags=['Venues'], summary='List all venues'),
    retrieve=extend_schema(tags=['Venues'], summary='Get venue details'),
    create=extend_schema(tags=['Venues'], summary='Create venue (Admin only)'),
    update=extend_schema(tags=['Venues'], summary='Update venue (Admin/Manager)'),
    partial_update=extend_schema(tags=['Venues'], summary='Partial update venue'),
    destroy=extend_schema(tags=['Venues'], summary='Delete venue (Admin only)'),
)
class VenueViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Venue

    Public read access to venue information.
    Admins can create/update/delete venues.
    Venue managers can update their venues.
    """

    queryset = Venue.objects.filter(is_active=True).order_by('name')
    serializer_class = VenueSerializer

    def get_permissions(self):
        """
        Return permissions based on action.
        """
        if self.action in ['list', 'retrieve', 'schedule']:
            return [AllowAny()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), IsVenueManager()]
        elif self.action in ['create', 'destroy']:
            return [IsAuthenticated(), IsAdminOrReadOnly()]
        return [IsAuthenticated()]

    @extend_schema(tags=['Venues'], summary='Get venue schedule', description='View upcoming events at this venue')
    @action(detail=True, methods=['get'], url_path='schedule')
    def schedule(self, request, pk=None):
        """
        View upcoming events at this venue.
        """
        venue = self.get_object()
        events = Event.objects.filter(
            venue=venue,
            status='PUBLISHED',
            is_active=True,
            ends_at__gt=timezone.now()
        ).select_related('organization', 'category').order_by('starts_at')

        page = self.paginate_queryset(events)
        if page is not None:
            serializer = EventListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data)


# =============================================================================
# Organization ViewSet
# =============================================================================

@extend_schema_view(
    list=extend_schema(tags=['Organizations'], summary='List all organizations'),
    retrieve=extend_schema(tags=['Organizations'], summary='Get organization details'),
    create=extend_schema(tags=['Organizations'], summary='Create organization (Admin only)'),
    update=extend_schema(tags=['Organizations'], summary='Update organization (Owner/Manager)'),
    partial_update=extend_schema(tags=['Organizations'], summary='Partial update organization'),
    destroy=extend_schema(tags=['Organizations'], summary='Delete organization (Admin only)'),
)
class OrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Organization model

    Public read access to organization information.
    Admins can create organizations.
    Organization owners/managers can update and manage members.
    """

    queryset = Organization.objects.filter(is_active=True).order_by('name')
    serializer_class = OrganizationSerializer

    def get_permissions(self):
        """
        Return permissions based on action.
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), IsOrganizationOwnerOrManager()]
        elif self.action in ['create', 'destroy']:
            return [IsAuthenticated(), IsAdminOrReadOnly()]
        elif self.action in ['events', 'members']:
            return [IsAuthenticated(), IsOrganizationMember()]
        elif self.action == 'add_member':
            return [IsAuthenticated(), IsOrganizationOwnerOrManager()]
        return [IsAuthenticated()]

    @extend_schema(tags=['Organizations'], summary='List organization events', description='List organization events (members see drafts too)')
    @action(detail=True, methods=['get'], url_path='events')
    def events(self, request, pk=None):
        """
        List organization's events (including drafts for members).
        """
        organization = self.get_object()
        user = request.user

        # Members see all events, others see only published
        if user.is_staff or user.is_superuser or OrganizationMembership.objects.filter(
            user=user, organization=organization
        ).exists():
            events = Event.objects.filter(
                organization=organization,
                is_active=True
            )
        else:
            events = Event.objects.filter(
                organization=organization,
                status='PUBLISHED',
                is_active=True
            )

        events = events.select_related('venue', 'category').order_by('-created_at')

        page = self.paginate_queryset(events)
        if page is not None:
            serializer = EventListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data)

    @extend_schema(tags=['Organizations'], summary='List organization members', description='List organization members (members only)')
    @action(detail=True, methods=['get'], url_path='members')
    def members(self, request, pk=None):
        """
        List organization members.
        Only organization members can view the member list.
        """
        organization = self.get_object()
        memberships = OrganizationMembership.objects.filter(
            organization=organization
        ).select_related('user').order_by('role', 'created_at')

        page = self.paginate_queryset(memberships)
        if page is not None:
            serializer = OrganizationMembershipSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = OrganizationMembershipSerializer(memberships, many=True)
        return Response(serializer.data)

    @extend_schema(tags=['Organizations'], summary='Add organization member', description='Add a member by email (owners/managers only)')
    @action(detail=True, methods=['post'], url_path='add-member')
    def add_member(self, request, pk=None):
        """
        Add a member to the organization.
        Only owners/managers can add members.
        """
        organization = self.get_object()
        data = request.data.copy()
        data['organization'] = organization.pk

        serializer = OrganizationMembershipCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()

        output_serializer = OrganizationMembershipSerializer(membership)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


# =============================================================================
# Event ViewSet
# =============================================================================

@extend_schema_view(
    list=extend_schema(tags=['Events'], summary='List published events'),
    retrieve=extend_schema(tags=['Events'], summary='Get event details'),
    create=extend_schema(tags=['Events'], summary='Create event (Organizer/Admin)'),
    update=extend_schema(tags=['Events'], summary='Update event (Organizer/Admin)'),
    partial_update=extend_schema(tags=['Events'], summary='Partial update event'),
    destroy=extend_schema(tags=['Events'], summary='Delete event (Organizer/Admin)'),
)
class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Event model.

    Public users can browse published events.
    Organizers can manage their organization's events.
    Admins have full access.
    """

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EventFilter
    search_fields = ['title', 'description']
    ordering_fields = ['starts_at', 'created_at', 'title']
    ordering = ['starts_at']

    def get_permissions(self):
        """
        Return permissions based on action.
        """
        if self.action in ['list', 'retrieve', 'available_tickets']:
            return [AllowAny()]
        elif self.action == 'create':
            return [IsAuthenticated(), IsOrganizerOrAdmin()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageEvent()]
        elif self.action == 'publish':
            return [IsAuthenticated(), CanPublishEvent()]
        elif self.action == 'cancel_event':
            return [IsAuthenticated(), CanManageEvent()]
        elif self.action == 'my_events':
            return [IsAuthenticated(), IsOrganizerOrAdmin()]
        elif self.action == 'event_bookings':
            return [IsAuthenticated(), IsOrganizationMember()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'retrieve':
            return EventDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EventManageSerializer
        elif self.action == 'publish':
            return EventPublishSerializer
        elif self.action == 'cancel_event':
            return EventCancelEventSerializer
        elif self.action == 'event_bookings':
            return BookingAdminSerializer
        return EventListSerializer

    def get_queryset(self):
        """
        Filter queryset based on action and user role.
        """
        base_qs = Event.objects.select_related(
            'organization', 'venue', 'category'
        )

        user = self.request.user

        if self.action == 'my_events':
            # Organizer's events via membership
            if user.is_authenticated:
                if user.is_staff or user.is_superuser:
                    return base_qs.order_by('-created_at')
                org_ids = OrganizationMembership.objects.filter(
                    user=user
                ).values_list('organization_id', flat=True)
                return base_qs.filter(organization_id__in=org_ids).order_by('-created_at')
            return base_qs.none()

        if self.action == 'list':
            # Public: only published, active, future events
            return base_qs.filter(
                status='PUBLISHED',
                is_active=True,
                ends_at__gt=timezone.now()
            ).order_by('starts_at')

        if self.action == 'retrieve':
            # For detail, allow org members to see drafts
            return base_qs.prefetch_related('tickets')

        # For management actions, return all events (permissions will filter)
        return base_qs

    @extend_schema(tags=['Events'], summary='Get available tickets', description='List ticket tiers with remaining inventory')
    @action(detail=True, methods=['get'], url_path='available-tickets')
    def available_tickets(self, request, pk=None):
        """
        Get available ticket tiers for a specific event.
        """
        event = self.get_object()
        available_tickets = event.tickets.filter(
            quota__gt=models.F('sold')
        ).order_by('price')
        serializer = TicketListSerializer(available_tickets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(tags=['Events'], summary='List my events', description="List events for organizer's organizations (Organizers only)")
    @action(detail=False, methods=['get'], url_path='my-events')
    def my_events(self, request):
        """
        List events for the current organizer's organizations.
        Includes drafts and all statuses.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = EventListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = EventListSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(tags=['Events'], summary='Publish event', description='Publish a draft event (Organizer/Admin)')
    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        """
        Publish a draft event.
        Only organization owners/managers can publish.
        """
        event = self.get_object()
        serializer = EventPublishSerializer(event, data={})
        serializer.is_valid(raise_exception=True)
        updated_event = serializer.save()
        return Response({
            'message': 'Event published successfully.',
            'event': EventDetailSerializer(updated_event).data
        }, status=status.HTTP_200_OK)

    @extend_schema(tags=['Events'], summary='Cancel event', description='Cancel an event (Organizer/Admin)')
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_event(self, request, pk=None):
        """
        Cancel an event.
        Only organization owners/managers can cancel.
        """
        event = self.get_object()
        serializer = EventCancelEventSerializer(event, data={})
        serializer.is_valid(raise_exception=True)
        updated_event = serializer.save()
        return Response({
            'message': 'Event cancelled successfully.',
            'event': EventDetailSerializer(updated_event).data
        }, status=status.HTTP_200_OK)

    @extend_schema(tags=['Events'], summary='List event bookings', description='View bookings for this event (Org members only)')
    @action(detail=True, methods=['get'], url_path='bookings')
    def event_bookings(self, request, pk=None):
        """
        View bookings for this event.
        Only organization members can view.
        """
        event = self.get_object()
        bookings = Booking.objects.filter(
            event_ticket__event=event
        ).select_related(
            'user', 'event_ticket'
        ).order_by('-created_at')

        page = self.paginate_queryset(bookings)
        if page is not None:
            serializer = BookingAdminSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = BookingAdminSerializer(bookings, many=True)
        return Response(serializer.data)


# =============================================================================
# Booking ViewSet
# =============================================================================

@extend_schema_view(
    list=extend_schema(tags=['Bookings'], summary='List bookings (own or all for staff)'),
    retrieve=extend_schema(tags=['Bookings'], summary='Get booking details'),
    create=extend_schema(tags=['Bookings'], summary='Create booking (Customer only)'),
)
class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Booking model.

    Customers can create bookings and view their own.
    Support staff can view all bookings and perform refunds.
    Organization members can confirm bookings for their events.
    """

    def get_permissions(self):
        """
        Return permissions based on action.
        """
        if self.action == 'create':
            # Only customers can create bookings
            return [IsAuthenticated(), IsCustomer()]
        elif self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        elif self.action == 'cancel':
            return [IsAuthenticated()]
        elif self.action == 'confirm':
            return [IsAuthenticated(), IsSupportOrAdmin()]
        elif self.action == 'refund':
            return [IsAuthenticated(), CanRefundBooking()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        Filter bookings based on user role.

        Customers see only their own bookings.
        Support staff/admins see all bookings.
        """
        user = self.request.user
        base_qs = Booking.objects.select_related(
            'user',
            'event_ticket',
            'event_ticket__event',
            'event_ticket__event__venue',
            'event_ticket__event__organization',
            'event_ticket__event__category'
        ).order_by('-created_at')

        # Staff and superusers see all bookings
        if user.is_staff or user.is_superuser:
            return base_qs

        # Support staff see all bookings
        if user.groups.filter(name='Support Staff').exists():
            return base_qs

        # Regular users see only their own bookings
        return base_qs.filter(user=user)

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action and user role.
        """
        user = self.request.user

        if self.action == 'create':
            return BookingCreateSerializer
        elif self.action == 'cancel':
            return BookingCancelSerializer
        elif self.action == 'confirm':
            return BookingConfirmSerializer
        elif self.action == 'refund':
            return BookingRefundSerializer

        # For list/retrieve, use admin serializer for staff/support
        if user.is_staff or user.is_superuser or user.groups.filter(name='Support Staff').exists():
            if self.action == 'retrieve':
                return BookingAdminSerializer
            return BookingAdminSerializer

        if self.action == 'retrieve':
            return BookingDetailSerializer
        return BookingListSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new booking.

        Only users in the Customers group can create bookings.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()

        output_serializer = BookingDetailSerializer(booking)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @extend_schema(tags=['Bookings'], summary='Cancel booking', description='Cancel a booking and return tickets to inventory')
    @action(detail=True, methods=['patch'], url_path='cancel')
    def cancel(self, request, pk=None):
        """
        Cancel a booking and return tickets to inventory.

        Users can cancel their own PENDING/CONFIRMED bookings.
        Support staff can cancel any booking.
        """
        booking = self.get_object()

        # Check if user can cancel this booking
        user = request.user
        if not (user.is_staff or user.is_superuser or
                user.groups.filter(name='Support Staff').exists()):
            if booking.user != user:
                return Response(
                    {'detail': 'You can only cancel your own bookings.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = self.get_serializer(booking, data={})
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()

        output_serializer = BookingDetailSerializer(updated_booking)
        return Response({
            'message': 'Booking cancelled successfully.',
            'booking': output_serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(tags=['Bookings'], summary='Confirm booking', description='Confirm a pending booking (Support staff only)')
    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        """
        Confirm a pending booking.

        Only Support staff or organization members can confirm.
        """
        booking = self.get_object()
        serializer = self.get_serializer(booking, data={})
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()

        output_serializer = BookingDetailSerializer(updated_booking)
        return Response({
            'message': 'Booking confirmed successfully.',
            'booking': output_serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(tags=['Bookings'], summary='Refund booking', description='Refund a booking (Support staff/Org managers only)')
    @action(detail=True, methods=['post'], url_path='refund')
    def refund(self, request, pk=None):
        """
        Refund a booking (cancel and return tickets).

        Only Support staff or organization managers can refund.
        """
        booking = self.get_object()
        serializer = BookingRefundSerializer(booking, data={})
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()

        output_serializer = BookingAdminSerializer(updated_booking)
        return Response({
            'message': 'Booking refunded successfully.',
            'booking': output_serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Disable DELETE method for bookings.
        """
        return Response(
            {'detail': 'Use the cancel or refund endpoint instead.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


# =============================================================================
# Ticket ViewSet
# =============================================================================

@extend_schema_view(
    list=extend_schema(tags=['Tickets'], summary='List ticket tiers'),
    retrieve=extend_schema(tags=['Tickets'], summary='Get ticket tier details'),
    create=extend_schema(tags=['Tickets'], summary='Create ticket tier (Organizer/Admin)'),
    update=extend_schema(tags=['Tickets'], summary='Update ticket tier (Organizer/Admin)'),
    partial_update=extend_schema(tags=['Tickets'], summary='Partial update ticket tier'),
    destroy=extend_schema(tags=['Tickets'], summary='Delete ticket tier (Organizer/Admin)'),
)
class TicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EventsTicket model.

    Public read access to ticket tiers.
    Organizers can create/update/delete tickets for their events.
    """

    def get_permissions(self):
        """
        Return permissions based on action.
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOrganizerOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        Filter tickets by event if event_pk is provided.
        """
        queryset = EventsTicket.objects.select_related('event', 'event__organization')

        # Filter by event if in nested route
        event_pk = self.kwargs.get('event_pk')
        if event_pk:
            queryset = queryset.filter(event_id=event_pk)

        return queryset.order_by('price')

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action in ['create', 'update', 'partial_update']:
            return TicketManageSerializer
        return TicketListSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a ticket tier for an event.
        Validates organization membership.
        """
        data = request.data.copy()

        # If in nested route, use event from URL
        event_pk = self.kwargs.get('event_pk')
        if event_pk:
            data['event'] = event_pk

        serializer = TicketManageSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()

        output_serializer = TicketManageSerializer(ticket)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Update a ticket tier.
        Validates organization membership.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Validate user can manage this event's tickets
        user = request.user
        if not (user.is_staff or user.is_superuser):
            if not OrganizationMembership.objects.filter(
                user=user,
                organization=instance.event.organization,
                role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER]
            ).exists():
                return Response(
                    {'detail': "You must be an owner or manager of the event's organization."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = TicketManageSerializer(
            instance, data=request.data, partial=partial, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()

        return Response(TicketManageSerializer(ticket).data)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a ticket tier.
        Only if no tickets have been sold.
        """
        instance = self.get_object()

        # Validate user can manage this event's tickets
        user = request.user
        if not (user.is_staff or user.is_superuser):
            if not OrganizationMembership.objects.filter(
                user=user,
                organization=instance.event.organization,
                role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER]
            ).exists():
                return Response(
                    {'detail': "You must be an owner or manager of the event's organization."},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Check if tickets have been sold
        if instance.sold > 0:
            return Response(
                {'detail': f'Cannot delete ticket tier with {instance.sold} tickets sold.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
