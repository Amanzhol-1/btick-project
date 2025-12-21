# Python modules
from typing import Any

# Django modules
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

# Django Rest Framework modules
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

# Third-party modules
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)
from rest_framework.filters import SearchFilter, OrderingFilter

# Project modules
from apps.btick.filters import EventFilter
from apps.btick.models import (
    Booking,
    BookingStatus,
    Event,
    EventCategory,
    EventsTicket,
    EventStatus,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    Venue,
    VenueMembership,
)
from apps.btick.permissions import (
    CanManageEvent,
    CanPublishEvent,
    CanRefundBooking,
    IsAdminOrReadOnly,
    IsCustomer,
    IsOrganizationMember,
    IsOrganizationOwnerOrManager,
    IsOrganizerOrAdmin,
    IsSupportOrAdmin,
    IsVenueManager,
    IsVenueMember,
)
from apps.btick.serializers import (
    BookingAdminSerializer,
    BookingCancelSerializer,
    BookingConfirmSerializer,
    BookingCreateSerializer,
    BookingDetailSerializer,
    BookingListSerializer,
    BookingRefundSerializer,
    EventCancelEventSerializer,
    EventCategorySerializer,
    EventDetailSerializer,
    EventListSerializer,
    EventManageSerializer,
    EventPublishSerializer,
    OrganizationMembershipCreateSerializer,
    OrganizationMembershipSerializer,
    OrganizationSerializer,
    TicketListSerializer,
    TicketManageSerializer,
    VenueMembershipSerializer,
    VenueSerializer,
)


# =============================================================================
# Category ViewSet
# =============================================================================

@extend_schema_view(
    list=extend_schema(tags=["Categories"], summary="List all event categories"),
    retrieve=extend_schema(tags=["Categories"], summary="Get category details"),
    create=extend_schema(tags=["Categories"], summary="Create category (Admin only)"),
    partial_update=extend_schema(tags=["Categories"], summary="Partial update category (Admin only)"),
    destroy=extend_schema(tags=["Categories"], summary="Delete category (Admin only)"),
)
class EventCategoryViewSet(ViewSet):
    """
    ViewSet for EventCategory model.

    Provides read-only access to event categories for all users.
    Only admins can create/update/delete categories.
    """

    permission_classes: list = [IsAdminOrReadOnly]

    def get_permissions(self) -> list:
        """Return permissions based on action."""
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminOrReadOnly()]

    def list(self, request: Request) -> Response:
        """Get all event categories."""
        queryset: QuerySet[EventCategory] = EventCategory.objects.filter(
            is_active=True,
        ).order_by("name")
        serializer = EventCategorySerializer(queryset, many=True)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    def retrieve(self, request: Request, pk: str) -> Response:
        """Get category details."""
        category: EventCategory | None = EventCategory.objects.filter(
            pk=pk,
            is_active=True,
        ).first()
        if not category:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = EventCategorySerializer(category)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    def create(self, request: Request) -> Response:
        """Create a new category (Admin only)."""
        serializer = EventCategorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        serializer.save()
        return Response(
            status=status.HTTP_201_CREATED,
            data=serializer.data,
        )

    def partial_update(self, request: Request, pk: str) -> Response:
        """Update a category (Admin only)."""
        category: EventCategory | None = EventCategory.objects.filter(
            pk=pk,
            is_active=True,
        ).first()
        if not category:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = EventCategorySerializer(
            category,
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        serializer.save()
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    def destroy(self, request: Request, pk: str) -> Response:
        """Delete a category (Admin only)."""
        category: EventCategory | None = EventCategory.objects.filter(
            pk=pk,
            is_active=True,
        ).first()
        if not category:
            return Response(status=status.HTTP_404_NOT_FOUND)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================================================
# Venue ViewSet
# =============================================================================

@extend_schema_view(
    list=extend_schema(tags=["Venues"], summary="List all venues"),
    retrieve=extend_schema(tags=["Venues"], summary="Get venue details"),
    create=extend_schema(tags=["Venues"], summary="Create venue (Admin only)"),
    partial_update=extend_schema(tags=["Venues"], summary="Partial update venue"),
    destroy=extend_schema(tags=["Venues"], summary="Delete venue (Admin only)"),
)
class VenueViewSet(ViewSet):
    """
    ViewSet for Venue model.

    Public read access to venue information.
    Admins can create/update/delete venues.
    Venue managers can update their venues.
    """

    def get_permissions(self) -> list:
        """Return permissions based on action."""
        if self.action in ["list", "retrieve", "schedule"]:
            return [AllowAny()]
        elif self.action in ["partial_update"]:
            return [IsAuthenticated(), IsVenueManager()]
        elif self.action in ["create", "destroy"]:
            return [IsAuthenticated(), IsAdminOrReadOnly()]
        return [IsAuthenticated()]

    def list(self, request: Request) -> Response:
        """Get all venues."""
        queryset: QuerySet[Venue] = Venue.objects.filter(
            is_active=True,
        ).order_by("name")
        serializer = VenueSerializer(queryset, many=True)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    def retrieve(self, request: Request, pk: str) -> Response:
        """Get venue details."""
        venue: Venue | None = Venue.objects.filter(
            pk=pk,
            is_active=True,
        ).first()
        if not venue:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = VenueSerializer(venue)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    def create(self, request: Request) -> Response:
        """Create a new venue (Admin only)."""
        serializer = VenueSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        serializer.save()
        return Response(
            status=status.HTTP_201_CREATED,
            data=serializer.data,
        )

    def partial_update(self, request: Request, pk: str) -> Response:
        """Update a venue (Admin/Manager)."""
        venue: Venue | None = Venue.objects.filter(
            pk=pk,
            is_active=True,
        ).first()
        if not venue:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = VenueSerializer(
            venue,
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        serializer.save()
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    def destroy(self, request: Request, pk: str) -> Response:
        """Delete a venue (Admin only)."""
        venue: Venue | None = Venue.objects.filter(
            pk=pk,
            is_active=True,
        ).first()
        if not venue:
            return Response(status=status.HTTP_404_NOT_FOUND)
        venue.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Venues"],
        summary="Get venue schedule",
        description="View upcoming events at this venue",
    )
    @action(detail=True, methods=["GET"], url_path="schedule")
    def schedule(self, request: Request, pk: str) -> Response:
        """View upcoming events at this venue."""
        venue: Venue | None = Venue.objects.filter(
            pk=pk,
            is_active=True,
        ).first()
        if not venue:
            return Response(status=status.HTTP_404_NOT_FOUND)

        events: QuerySet[Event] = Event.objects.filter(
            venue=venue,
            status=EventStatus.PUBLISHED,
            is_active=True,
            ends_at__gt=timezone.now(),
        ).select_related("organization", "category").order_by("starts_at")

        serializer = EventListSerializer(events, many=True)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )


# =============================================================================
# Organization ViewSet
# =============================================================================

@extend_schema_view(
    list=extend_schema(tags=["Organizations"], summary="List all organizations"),
    retrieve=extend_schema(tags=["Organizations"], summary="Get organization details"),
    create=extend_schema(tags=["Organizations"], summary="Create organization (Admin only)"),
    partial_update=extend_schema(tags=["Organizations"], summary="Partial update organization"),
    destroy=extend_schema(tags=["Organizations"], summary="Delete organization (Admin only)"),
)
class OrganizationViewSet(ViewSet):
    """
    ViewSet for Organization model.

    Public read access to organization information.
    Admins can create organizations.
    Organization owners/managers can update and manage members.
    """

    def get_permissions(self) -> list:
        """Return permissions based on action."""
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        elif self.action in ["partial_update"]:
            return [IsAuthenticated(), IsOrganizationOwnerOrManager()]
        elif self.action in ["create", "destroy"]:
            return [IsAuthenticated(), IsAdminOrReadOnly()]
        elif self.action in ["events", "members"]:
            return [IsAuthenticated(), IsOrganizationMember()]
        elif self.action == "add_member":
            return [IsAuthenticated(), IsOrganizationOwnerOrManager()]
        return [IsAuthenticated()]

    def list(self, request: Request) -> Response:
        """Get all organizations."""
        queryset: QuerySet[Organization] = Organization.objects.filter(
            is_active=True,
        ).order_by("name")
        serializer = OrganizationSerializer(queryset, many=True)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    def retrieve(self, request: Request, pk: str) -> Response:
        """Get organization details."""
        organization: Organization | None = Organization.objects.filter(
            pk=pk,
            is_active=True,
        ).first()
        if not organization:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = OrganizationSerializer(organization)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    def create(self, request: Request) -> Response:
        """Create a new organization (Admin only)."""
        serializer = OrganizationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        serializer.save()
        return Response(
            status=status.HTTP_201_CREATED,
            data=serializer.data,
        )

    def partial_update(self, request: Request, pk: str) -> Response:
        """Update an organization (Owner/Manager)."""
        organization: Organization | None = Organization.objects.filter(
            pk=pk,
            is_active=True,
        ).first()
        if not organization:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = OrganizationSerializer(
            organization,
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        serializer.save()
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    def destroy(self, request: Request, pk: str) -> Response:
        """Delete an organization (Admin only)."""
        organization: Organization | None = Organization.objects.filter(
            pk=pk,
            is_active=True,
        ).first()
        if not organization:
            return Response(status=status.HTTP_404_NOT_FOUND)
        organization.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Organizations"],
        summary="List organization events",
        description="List organization events (members see drafts too)",
    )
    @action(detail=True, methods=["GET"], url_path="events")
    def events(self, request: Request, pk: str) -> Response:
        """List organization's events (including drafts for members)."""
        organization: Organization | None = Organization.objects.filter(
            pk=pk,
            is_active=True,
        ).first()
        if not organization:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user = request.user

        # Members see all events, others see only published
        if user.is_staff or user.is_superuser or OrganizationMembership.objects.filter(
            user=user,
            organization=organization,
        ).exists():
            events: QuerySet[Event] = Event.objects.filter(
                organization=organization,
                is_active=True,
            )
        else:
            events = Event.objects.filter(
                organization=organization,
                status=EventStatus.PUBLISHED,
                is_active=True,
            )

        events = events.select_related("venue", "category").order_by("-created_at")
        serializer = EventListSerializer(events, many=True)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    @extend_schema(
        tags=["Organizations"],
        summary="List organization members",
        description="List organization members (members only)",
    )
    @action(detail=True, methods=["GET"], url_path="members")
    def members(self, request: Request, pk: str) -> Response:
        """List organization members."""
        organization: Organization | None = Organization.objects.filter(
            pk=pk,
            is_active=True,
        ).first()
        if not organization:
            return Response(status=status.HTTP_404_NOT_FOUND)

        memberships: QuerySet[OrganizationMembership] = OrganizationMembership.objects.filter(
            organization=organization,
        ).select_related("user").order_by("role", "created_at")

        serializer = OrganizationMembershipSerializer(memberships, many=True)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    @extend_schema(
        tags=["Organizations"],
        summary="Add organization member",
        description="Add a member by email (owners/managers only)",
    )
    @action(detail=True, methods=["POST"], url_path="add-member")
    def add_member(self, request: Request, pk: str) -> Response:
        """Add a member to the organization."""
        organization: Organization | None = Organization.objects.filter(
            pk=pk,
            is_active=True,
        ).first()
        if not organization:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        data["organization"] = organization.pk

        serializer = OrganizationMembershipCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        membership = serializer.save()

        output_serializer = OrganizationMembershipSerializer(membership)
        return Response(
            status=status.HTTP_201_CREATED,
            data=output_serializer.data,
        )


# =============================================================================
# Event ViewSet
# =============================================================================

@extend_schema_view(
    list=extend_schema(tags=["Events"], summary="List published events"),
    retrieve=extend_schema(tags=["Events"], summary="Get event details"),
    create=extend_schema(tags=["Events"], summary="Create event (Organizer/Admin)"),
    partial_update=extend_schema(tags=["Events"], summary="Partial update event"),
    destroy=extend_schema(tags=["Events"], summary="Delete event (Organizer/Admin)"),
)
class EventViewSet(ViewSet):
    """
    ViewSet for Event model.

    Public users can browse published events.
    Organizers can manage their organization's events.
    Admins have full access.
    """

    filter_backends: list = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EventFilter
    search_fields: list[str] = ["title", "description"]
    ordering_fields: list[str] = ["starts_at", "created_at", "title"]
    ordering: list[str] = ["starts_at"]

    def get_permissions(self) -> list:
        """Return permissions based on action."""
        if self.action in ["list", "retrieve", "available_tickets"]:
            return [AllowAny()]
        elif self.action == "create":
            return [IsAuthenticated(), IsOrganizerOrAdmin()]
        elif self.action in ["partial_update", "destroy"]:
            return [IsAuthenticated(), CanManageEvent()]
        elif self.action == "publish":
            return [IsAuthenticated(), CanPublishEvent()]
        elif self.action == "cancel_event":
            return [IsAuthenticated(), CanManageEvent()]
        elif self.action == "my_events":
            return [IsAuthenticated(), IsOrganizerOrAdmin()]
        elif self.action == "event_bookings":
            return [IsAuthenticated(), IsOrganizationMember()]
        return [IsAuthenticated()]

    def _get_base_queryset(self) -> QuerySet[Event]:
        """Get base queryset with common optimizations."""
        return Event.objects.select_related(
            "organization",
            "venue",
            "category",
        )

    def list(self, request: Request) -> Response:
        """Get all published events."""
        queryset: QuerySet[Event] = self._get_base_queryset().filter(
            status=EventStatus.PUBLISHED,
            is_active=True,
            ends_at__gt=timezone.now(),
        ).order_by("starts_at")

        serializer = EventListSerializer(queryset, many=True)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    def retrieve(self, request: Request, pk: str) -> Response:
        """Get event details."""
        event: Event | None = self._get_base_queryset().prefetch_related(
            "tickets",
        ).filter(pk=pk).first()
        if not event:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = EventDetailSerializer(event)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    def create(self, request: Request) -> Response:
        """Create a new event (Organizer/Admin)."""
        serializer = EventManageSerializer(
            data=request.data,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        event = serializer.save()
        output_serializer = EventDetailSerializer(event)
        return Response(
            status=status.HTTP_201_CREATED,
            data=output_serializer.data,
        )

    def partial_update(self, request: Request, pk: str) -> Response:
        """Update an event (Organizer/Admin)."""
        event: Event | None = Event.objects.filter(pk=pk).first()
        if not event:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Check permission
        user = request.user
        if not (user.is_staff or user.is_superuser):
            if not OrganizationMembership.objects.filter(
                user=user,
                organization=event.organization,
                role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER],
            ).exists():
                return Response(
                    status=status.HTTP_403_FORBIDDEN,
                    data={"detail": "You must be an owner or manager of the event's organization."},
                )

        serializer = EventManageSerializer(
            event,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        updated_event = serializer.save()
        output_serializer = EventDetailSerializer(updated_event)
        return Response(
            status=status.HTTP_200_OK,
            data=output_serializer.data,
        )

    def destroy(self, request: Request, pk: str) -> Response:
        """Delete an event (Organizer/Admin)."""
        event: Event | None = Event.objects.filter(pk=pk).first()
        if not event:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Check permission
        user = request.user
        if not (user.is_staff or user.is_superuser):
            if not OrganizationMembership.objects.filter(
                user=user,
                organization=event.organization,
                role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER],
            ).exists():
                return Response(
                    status=status.HTTP_403_FORBIDDEN,
                    data={"detail": "You must be an owner or manager of the event's organization."},
                )

        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Events"],
        summary="Get available tickets",
        description="List ticket tiers with remaining inventory",
    )
    @action(detail=True, methods=["GET"], url_path="available-tickets")
    def available_tickets(self, request: Request, pk: str) -> Response:
        """Get available ticket tiers for a specific event."""
        event: Event | None = Event.objects.filter(pk=pk).first()
        if not event:
            return Response(status=status.HTTP_404_NOT_FOUND)

        available_tickets: QuerySet[EventsTicket] = event.tickets.filter(
            quota__gt=models.F("sold"),
        ).order_by("price")

        serializer = TicketListSerializer(available_tickets, many=True)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    @extend_schema(
        tags=["Events"],
        summary="List my events",
        description="List events for organizer's organizations (Organizers only)",
    )
    @action(detail=False, methods=["GET"], url_path="my-events")
    def my_events(self, request: Request) -> Response:
        """List events for the current organizer's organizations."""
        user = request.user

        if user.is_staff or user.is_superuser:
            queryset: QuerySet[Event] = self._get_base_queryset().order_by("-created_at")
        else:
            org_ids = OrganizationMembership.objects.filter(
                user=user,
            ).values_list("organization_id", flat=True)
            queryset = self._get_base_queryset().filter(
                organization_id__in=org_ids,
            ).order_by("-created_at")

        serializer = EventListSerializer(queryset, many=True)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    @extend_schema(
        tags=["Events"],
        summary="Publish event",
        description="Publish a draft event (Organizer/Admin)",
    )
    @action(detail=True, methods=["POST"], url_path="publish")
    def publish(self, request: Request, pk: str) -> Response:
        """Publish a draft event."""
        event: Event | None = Event.objects.filter(pk=pk).first()
        if not event:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = EventPublishSerializer(event, data={})
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        updated_event = serializer.save()
        return Response(
            status=status.HTTP_200_OK,
            data={
                "message": "Event published successfully.",
                "event": EventDetailSerializer(updated_event).data,
            },
        )

    @extend_schema(
        tags=["Events"],
        summary="Cancel event",
        description="Cancel an event (Organizer/Admin)",
    )
    @action(detail=True, methods=["POST"], url_path="cancel")
    def cancel_event(self, request: Request, pk: str) -> Response:
        """Cancel an event."""
        event: Event | None = Event.objects.filter(pk=pk).first()
        if not event:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = EventCancelEventSerializer(event, data={})
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        updated_event = serializer.save()
        return Response(
            status=status.HTTP_200_OK,
            data={
                "message": "Event cancelled successfully.",
                "event": EventDetailSerializer(updated_event).data,
            },
        )

    @extend_schema(
        tags=["Events"],
        summary="List event bookings",
        description="View bookings for this event (Org members only)",
    )
    @action(detail=True, methods=["GET"], url_path="bookings")
    def event_bookings(self, request: Request, pk: str) -> Response:
        """View bookings for this event."""
        event: Event | None = Event.objects.filter(pk=pk).first()
        if not event:
            return Response(status=status.HTTP_404_NOT_FOUND)

        bookings: QuerySet[Booking] = Booking.objects.filter(
            event_ticket__event=event,
        ).select_related(
            "user",
            "event_ticket",
        ).order_by("-created_at")

        serializer = BookingAdminSerializer(bookings, many=True)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )


# =============================================================================
# Booking ViewSet
# =============================================================================

@extend_schema_view(
    list=extend_schema(tags=["Bookings"], summary="List bookings (own or all for staff)"),
    retrieve=extend_schema(tags=["Bookings"], summary="Get booking details"),
    create=extend_schema(tags=["Bookings"], summary="Create booking (Customer only)"),
)
class BookingViewSet(ViewSet):
    """
    ViewSet for Booking model.

    Customers can create bookings and view their own.
    Support staff can view all bookings and perform refunds.
    Organization members can confirm bookings for their events.
    """

    def get_permissions(self) -> list:
        """Return permissions based on action."""
        if self.action == "create":
            return [IsAuthenticated(), IsCustomer()]
        elif self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        elif self.action == "cancel":
            return [IsAuthenticated()]
        elif self.action == "confirm":
            return [IsAuthenticated(), IsSupportOrAdmin()]
        elif self.action == "refund":
            return [IsAuthenticated(), CanRefundBooking()]
        return [IsAuthenticated()]

    def _get_base_queryset(self, user: Any) -> QuerySet[Booking]:
        """Get base queryset filtered by user role."""
        base_qs: QuerySet[Booking] = Booking.objects.select_related(
            "user",
            "event_ticket",
            "event_ticket__event",
            "event_ticket__event__venue",
            "event_ticket__event__organization",
            "event_ticket__event__category",
        ).order_by("-created_at")

        # Staff and superusers see all bookings
        if user.is_staff or user.is_superuser:
            return base_qs

        # Support staff see all bookings
        if user.groups.filter(name="Support Staff").exists():
            return base_qs

        # Regular users see only their own bookings
        return base_qs.filter(user=user)

    def _get_serializer_class_for_user(self, user: Any, action: str) -> type:
        """Return appropriate serializer based on action and user role."""
        if action == "create":
            return BookingCreateSerializer
        elif action == "cancel":
            return BookingCancelSerializer
        elif action == "confirm":
            return BookingConfirmSerializer
        elif action == "refund":
            return BookingRefundSerializer

        # For list/retrieve, use admin serializer for staff/support
        if user.is_staff or user.is_superuser or user.groups.filter(name="Support Staff").exists():
            return BookingAdminSerializer

        if action == "retrieve":
            return BookingDetailSerializer
        return BookingListSerializer

    def list(self, request: Request) -> Response:
        """Get all bookings (filtered by user role)."""
        queryset: QuerySet[Booking] = self._get_base_queryset(request.user)
        serializer_class = self._get_serializer_class_for_user(request.user, "list")
        serializer = serializer_class(queryset, many=True)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    def retrieve(self, request: Request, pk: str) -> Response:
        """Get booking details."""
        queryset: QuerySet[Booking] = self._get_base_queryset(request.user)
        booking: Booking | None = queryset.filter(pk=pk).first()
        if not booking:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer_class = self._get_serializer_class_for_user(request.user, "retrieve")
        serializer = serializer_class(booking)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    def create(self, request: Request) -> Response:
        """Create a new booking (Customer only)."""
        serializer = BookingCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        booking = serializer.save()
        output_serializer = BookingDetailSerializer(booking)
        return Response(
            status=status.HTTP_201_CREATED,
            data=output_serializer.data,
        )

    def destroy(self, request: Request, pk: str) -> Response:
        """Disable DELETE method for bookings."""
        return Response(
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
            data={"detail": "Use the cancel or refund endpoint instead."},
        )

    @extend_schema(
        tags=["Bookings"],
        summary="Cancel booking",
        description="Cancel a booking and return tickets to inventory",
    )
    @action(detail=True, methods=["PATCH"], url_path="cancel")
    def cancel(self, request: Request, pk: str) -> Response:
        """Cancel a booking and return tickets to inventory."""
        booking: Booking | None = Booking.objects.select_related(
            "user",
            "event_ticket",
        ).filter(pk=pk).first()
        if not booking:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Check if user can cancel this booking
        user = request.user
        if not (user.is_staff or user.is_superuser or user.groups.filter(name="Support Staff").exists()):
            if booking.user != user:
                return Response(
                    status=status.HTTP_403_FORBIDDEN,
                    data={"detail": "You can only cancel your own bookings."},
                )

        serializer = BookingCancelSerializer(booking, data={})
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        updated_booking = serializer.save()

        output_serializer = BookingDetailSerializer(updated_booking)
        return Response(
            status=status.HTTP_200_OK,
            data={
                "message": "Booking cancelled successfully.",
                "booking": output_serializer.data,
            },
        )

    @extend_schema(
        tags=["Bookings"],
        summary="Confirm booking",
        description="Confirm a pending booking (Support staff only)",
    )
    @action(detail=True, methods=["POST"], url_path="confirm")
    def confirm(self, request: Request, pk: str) -> Response:
        """Confirm a pending booking."""
        booking: Booking | None = Booking.objects.filter(pk=pk).first()
        if not booking:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = BookingConfirmSerializer(booking, data={})
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        updated_booking = serializer.save()

        output_serializer = BookingDetailSerializer(updated_booking)
        return Response(
            status=status.HTTP_200_OK,
            data={
                "message": "Booking confirmed successfully.",
                "booking": output_serializer.data,
            },
        )

    @extend_schema(
        tags=["Bookings"],
        summary="Refund booking",
        description="Refund a booking (Support staff/Org managers only)",
    )
    @action(detail=True, methods=["POST"], url_path="refund")
    def refund(self, request: Request, pk: str) -> Response:
        """Refund a booking (cancel and return tickets)."""
        booking: Booking | None = Booking.objects.filter(pk=pk).first()
        if not booking:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = BookingRefundSerializer(booking, data={})
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        updated_booking = serializer.save()

        output_serializer = BookingAdminSerializer(updated_booking)
        return Response(
            status=status.HTTP_200_OK,
            data={
                "message": "Booking refunded successfully.",
                "booking": output_serializer.data,
            },
        )


# =============================================================================
# Ticket ViewSet
# =============================================================================

@extend_schema_view(
    list=extend_schema(tags=["Tickets"], summary="List ticket tiers"),
    retrieve=extend_schema(tags=["Tickets"], summary="Get ticket tier details"),
    create=extend_schema(tags=["Tickets"], summary="Create ticket tier (Organizer/Admin)"),
    partial_update=extend_schema(tags=["Tickets"], summary="Partial update ticket tier"),
    destroy=extend_schema(tags=["Tickets"], summary="Delete ticket tier (Organizer/Admin)"),
)
class TicketViewSet(ViewSet):
    """
    ViewSet for EventsTicket model.

    Public read access to ticket tiers.
    Organizers can create/update/delete tickets for their events.
    """

    def get_permissions(self) -> list:
        """Return permissions based on action."""
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        elif self.action in ["create", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOrganizerOrAdmin()]
        return [IsAuthenticated()]

    def _get_queryset(self, event_pk: str | None = None) -> QuerySet[EventsTicket]:
        """Get queryset optionally filtered by event."""
        queryset: QuerySet[EventsTicket] = EventsTicket.objects.select_related(
            "event",
            "event__organization",
        )

        if event_pk:
            queryset = queryset.filter(event_id=event_pk)

        return queryset.order_by("price")

    def list(self, request: Request, event_pk: str | None = None) -> Response:
        """Get all ticket tiers."""
        queryset: QuerySet[EventsTicket] = self._get_queryset(event_pk)
        serializer = TicketListSerializer(queryset, many=True)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    def retrieve(self, request: Request, pk: str, event_pk: str | None = None) -> Response:
        """Get ticket tier details."""
        queryset: QuerySet[EventsTicket] = self._get_queryset(event_pk)
        ticket: EventsTicket | None = queryset.filter(pk=pk).first()
        if not ticket:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = TicketListSerializer(ticket)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    def create(self, request: Request, event_pk: str | None = None) -> Response:
        """Create a ticket tier for an event."""
        data = request.data.copy()

        # If in nested route, use event from URL
        if event_pk:
            data["event"] = event_pk

        serializer = TicketManageSerializer(
            data=data,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        ticket = serializer.save()

        output_serializer = TicketManageSerializer(ticket)
        return Response(
            status=status.HTTP_201_CREATED,
            data=output_serializer.data,
        )

    def partial_update(self, request: Request, pk: str, event_pk: str | None = None) -> Response:
        """Update a ticket tier."""
        queryset: QuerySet[EventsTicket] = self._get_queryset(event_pk)
        instance: EventsTicket | None = queryset.filter(pk=pk).first()
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Validate user can manage this event's tickets
        user = request.user
        if not (user.is_staff or user.is_superuser):
            if not OrganizationMembership.objects.filter(
                user=user,
                organization=instance.event.organization,
                role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER],
            ).exists():
                return Response(
                    status=status.HTTP_403_FORBIDDEN,
                    data={"detail": "You must be an owner or manager of the event's organization."},
                )

        serializer = TicketManageSerializer(
            instance,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors,
            )
        ticket = serializer.save()

        return Response(
            status=status.HTTP_200_OK,
            data=TicketManageSerializer(ticket).data,
        )

    def destroy(self, request: Request, pk: str, event_pk: str | None = None) -> Response:
        """Delete a ticket tier (only if no tickets sold)."""
        queryset: QuerySet[EventsTicket] = self._get_queryset(event_pk)
        instance: EventsTicket | None = queryset.filter(pk=pk).first()
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Validate user can manage this event's tickets
        user = request.user
        if not (user.is_staff or user.is_superuser):
            if not OrganizationMembership.objects.filter(
                user=user,
                organization=instance.event.organization,
                role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER],
            ).exists():
                return Response(
                    status=status.HTTP_403_FORBIDDEN,
                    data={"detail": "You must be an owner or manager of the event's organization."},
                )

        # Check if tickets have been sold
        if instance.sold > 0:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": f"Cannot delete ticket tier with {instance.sold} tickets sold."},
            )

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
