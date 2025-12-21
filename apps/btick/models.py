# Python modules

# Django modules
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import CASCADE, PROTECT, CheckConstraint, F, Q, UniqueConstraint

# Project modules
from apps.abstracts.models import BaseEntity


User = get_user_model()


class EventStatus(models.TextChoices):
    """
    Enum representing the lifecycle status of an Event.

    Values:
        DRAFT: Event is being prepared, not visible to public.
        PUBLISHED: Event is live and available for booking.
        CANCELLED: Event has been cancelled.
    """

    DRAFT = "DRAFT", "Draft"
    PUBLISHED = "PUBLISHED", "Published"
    CANCELLED = "CANCELLED", "Cancelled"


class BookingStatus(models.TextChoices):
    """
    Enum representing the status of a ticket Booking.

    Values:
        PENDING: Booking created but not yet confirmed (awaiting payment).
        CONFIRMED: Booking is confirmed and tickets are reserved.
        CANCELLED: Booking has been cancelled.
    """

    PENDING = "PENDING", "Pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    CANCELLED = "CANCELLED", "Cancelled"


class TicketType(models.TextChoices):
    """
    Enum representing available ticket tiers for events.

    Values:
        STANDARD: Regular admission ticket.
        VIP: Premium ticket with additional perks.
        EARLY_BIRD: Discounted ticket for early purchasers.
        STUDENT: Discounted ticket for students.
        GROUP: Discounted ticket for group bookings.
    """

    STANDARD = "STANDARD", "Standard"
    VIP = "VIP", "VIP"
    EARLY_BIRD = "EARLY_BIRD", "Early Bird"
    STUDENT = "STUDENT", "Student"
    GROUP = "GROUP", "Group"


class Organization(BaseEntity):
    """
    Represents an event organizer or company that hosts events.

    Organizations are the top-level entities that create and manage events.
    They can have multiple events associated with them.
    """

    # Class constants for field lengths
    NAME_MAX_LENGTH: int = 200

    name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        verbose_name="Organization name",
        help_text="Unique name of the organization",
    )
    website = models.URLField(
        blank=True,
        verbose_name="Website URL",
        help_text="Optional URL to the organization's website",
    )
    contact_email = models.EmailField(
        blank=True,
        verbose_name="Contact email",
        help_text="Optional email address for inquiries",
    )

    class Meta:
        """Meta options for Organization model."""

        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        permissions = [
            ("view_own_organization", "Can view own organization"),
            ("manage_organization_events", "Can manage organization events"),
            ("view_organization_analytics", "Can view organization analytics"),
            ("manage_organization_members", "Can manage organization members"),
        ]

    def __str__(self) -> str:
        """String representation."""
        return self.name

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Organization(id={self.pk}, name={self.name})"


class Venue(BaseEntity):
    """
    Represents a physical location where events are held.

    Venues define the location and maximum capacity for events.
    Multiple events can be scheduled at the same venue.
    """

    # Class constants for field lengths
    NAME_MAX_LENGTH: int = 200
    ADDRESS_MAX_LENGTH: int = 500

    name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        verbose_name="Venue name",
        help_text="Unique name of the venue",
    )
    address = models.CharField(
        max_length=ADDRESS_MAX_LENGTH,
        blank=True,
        verbose_name="Physical address",
        help_text="Optional physical address of the venue",
    )
    capacity = models.PositiveIntegerField(
        default=0,
        verbose_name="Maximum capacity",
        help_text="Maximum number of attendees the venue can hold",
    )

    class Meta:
        """Meta options for Venue model."""

        verbose_name = "Venue"
        verbose_name_plural = "Venues"
        permissions = [
            ("view_venue_schedule", "Can view events scheduled at venue"),
            ("manage_venue_capacity", "Can manage venue capacity"),
            ("view_venue_analytics", "Can view venue analytics"),
        ]

    def __str__(self) -> str:
        """String representation."""
        return self.name

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Venue(id={self.pk}, name={self.name})"


class EventCategory(BaseEntity):
    """
    Represents a classification category for events.

    Categories help organize and filter events by type
    (e.g., Concert, Conference, Workshop, Sports).
    """

    # Class constants for field lengths
    NAME_MAX_LENGTH: int = 64

    name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        verbose_name="Category name",
        help_text="Unique name of the event category",
    )

    class Meta:
        """Meta options for EventCategory model."""

        verbose_name = "Event Category"
        verbose_name_plural = "Event Categories"

    def __str__(self) -> str:
        """String representation."""
        return self.name

    def __repr__(self) -> str:
        """Developer representation."""
        return f"EventCategory(id={self.pk}, name={self.name})"


class Event(BaseEntity):
    """
    Represents a scheduled event that users can book tickets for.

    Events are the core entity of the ticketing system. Each event belongs
    to an organization, takes place at a venue, and has a category.
    """

    # Class constants for field lengths
    TITLE_MAX_LENGTH: int = 200
    STATUS_MAX_LENGTH: int = 12

    organization = models.ForeignKey(
        to=Organization,
        on_delete=PROTECT,
        related_name="events",
        verbose_name="Organization",
        help_text="The organization hosting this event",
    )
    venue = models.ForeignKey(
        to=Venue,
        on_delete=PROTECT,
        related_name="events",
        verbose_name="Venue",
        help_text="The location where the event takes place",
    )
    category = models.ForeignKey(
        to=EventCategory,
        on_delete=PROTECT,
        related_name="events",
        verbose_name="Category",
        help_text="The type/category of the event",
    )
    title = models.CharField(
        max_length=TITLE_MAX_LENGTH,
        unique=True,
        verbose_name="Event title",
        help_text="Unique title of the event",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Optional detailed description of the event",
    )
    starts_at = models.DateTimeField(
        verbose_name="Start date/time",
        help_text="Date and time when the event begins",
    )
    ends_at = models.DateTimeField(
        verbose_name="End date/time",
        help_text="Date and time when the event ends",
    )
    status = models.CharField(
        max_length=STATUS_MAX_LENGTH,
        choices=EventStatus.choices,
        default=EventStatus.DRAFT,
        verbose_name="Status",
        help_text="Current lifecycle status (DRAFT, PUBLISHED, CANCELLED)",
    )
    capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Event capacity",
        help_text="Optional override for venue capacity for this event",
    )

    class Meta:
        """Meta options for Event model."""

        verbose_name = "Event"
        verbose_name_plural = "Events"
        constraints = [
            CheckConstraint(
                check=Q(ends_at__gt=F("starts_at")),
                name="event_ends_after_start",
            ),
        ]
        permissions = [
            ("publish_event", "Can publish draft events"),
            ("cancel_event", "Can cancel events"),
            ("view_draft_events", "Can view unpublished/draft events"),
            ("view_event_analytics", "Can view event booking/sales analytics"),
            ("manage_event_tickets", "Can manage event ticket tiers"),
        ]

    def __str__(self) -> str:
        """String representation."""
        return self.title

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Event(id={self.pk}, title={self.title}, status={self.status})"


class EventsTicket(BaseEntity):
    """
    Represents a ticket tier available for purchase for an event.

    Each event can have multiple ticket types (e.g., Standard, VIP)
    with different prices and quotas. Tracks inventory via quota and sold.
    """

    # Class constants for field lengths
    TICKET_TYPE_MAX_LENGTH: int = 80

    event = models.ForeignKey(
        to=Event,
        on_delete=CASCADE,
        related_name="tickets",
        verbose_name="Event",
        help_text="The event this ticket belongs to",
    )
    ticket_type = models.CharField(
        max_length=TICKET_TYPE_MAX_LENGTH,
        choices=TicketType.choices,
        verbose_name="Ticket type",
        help_text="The tier of the ticket (STANDARD, VIP, etc.)",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Price",
        help_text="Price per ticket in the default currency",
    )
    quota = models.PositiveIntegerField(
        default=0,
        verbose_name="Quota",
        help_text="Total number of tickets available for sale",
    )
    sold = models.PositiveIntegerField(
        default=0,
        verbose_name="Sold",
        help_text="Number of tickets already sold",
    )

    class Meta:
        """Meta options for EventsTicket model."""

        verbose_name = "Events Ticket"
        verbose_name_plural = "Events Tickets"
        constraints = [
            UniqueConstraint(
                fields=["event", "ticket_type"],
                name="event_ticket_type_unique",
            ),
            CheckConstraint(
                check=Q(price__gte=0),
                name="ticker_price_non_negative",
            ),
            CheckConstraint(
                check=Q(quota__gte=0),
                name="quota_non_negative",
            ),
            CheckConstraint(
                check=Q(sold__gte=0),
                name="sold_non_negative",
            ),
        ]
        permissions = [
            ("view_ticket_inventory", "Can view ticket inventory (quota/sold)"),
            ("adjust_ticket_quota", "Can adjust ticket quota"),
            ("view_ticket_sales", "Can view ticket sales metrics"),
        ]

    def __str__(self) -> str:
        """String representation."""
        return self.ticket_type

    def __repr__(self) -> str:
        """Developer representation."""
        return f"EventsTicket(id={self.pk}, event_id={self.event_id}, type={self.ticket_type})"


class Booking(BaseEntity):
    """
    Represents a user's ticket reservation for an event.

    Bookings link users to event tickets and track the purchase status.
    A booking can be pending (awaiting payment), confirmed, or cancelled.
    """

    # Class constants for field lengths
    STATUS_MAX_LENGTH: int = 12

    user = models.ForeignKey(
        to=User,
        on_delete=CASCADE,
        related_name="bookings",
        verbose_name="User",
        help_text="The user who made the booking",
    )
    event_ticket = models.ForeignKey(
        to=EventsTicket,
        on_delete=PROTECT,
        related_name="bookings",
        verbose_name="Event ticket",
        help_text="The specific ticket type being booked",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Quantity",
        help_text="Number of tickets in this booking",
    )
    status = models.CharField(
        max_length=STATUS_MAX_LENGTH,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
        verbose_name="Status",
        help_text="Current status (PENDING, CONFIRMED, CANCELLED)",
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Expires at",
        help_text="Optional expiration time for pending bookings",
    )

    class Meta:
        """Meta options for Booking model."""

        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        constraints = [
            CheckConstraint(
                check=Q(quantity__gte=1),
                name="booking_quantity_gte_1",
            ),
        ]
        permissions = [
            ("view_own_bookings", "Can view own bookings only"),
            ("cancel_own_booking", "Can cancel own pending bookings"),
            ("view_event_bookings", "Can view all bookings for managed events"),
            ("confirm_booking", "Can confirm pending bookings"),
            ("refund_booking", "Can refund/cancel any booking"),
        ]

    def __str__(self) -> str:
        """String representation."""
        return f"Booking {self.pk}> {self.user_id} x{self.quantity} {self.event_ticket.ticket_type}"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Booking(id={self.pk}, user_id={self.user_id}, status={self.status})"


class OrganizationRole(models.TextChoices):
    """Roles for organization membership."""

    OWNER = "OWNER", "Owner"
    MANAGER = "MANAGER", "Manager"
    STAFF = "STAFF", "Staff"


class OrganizationMembership(BaseEntity):
    """
    Links users to organizations they manage or work for.

    Defines the relationship between users and organizations with specific roles.
    """

    # Class constants for field lengths
    ROLE_MAX_LENGTH: int = 20

    user = models.ForeignKey(
        to=User,
        on_delete=CASCADE,
        related_name="organization_memberships",
        verbose_name="User",
        help_text="The user who is a member",
    )
    organization = models.ForeignKey(
        to=Organization,
        on_delete=CASCADE,
        related_name="memberships",
        verbose_name="Organization",
        help_text="The organization they belong to",
    )
    role = models.CharField(
        max_length=ROLE_MAX_LENGTH,
        choices=OrganizationRole.choices,
        default=OrganizationRole.STAFF,
        verbose_name="Role",
        help_text="Their role within the organization (OWNER, MANAGER, STAFF)",
    )

    class Meta:
        """Meta options for OrganizationMembership model."""

        verbose_name = "Organization Membership"
        verbose_name_plural = "Organization Memberships"
        constraints = [
            UniqueConstraint(
                fields=["user", "organization"],
                name="unique_user_organization",
            ),
        ]

    def __str__(self) -> str:
        """String representation."""
        return f"{self.user.email} - {self.organization.name} ({self.role})"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"OrganizationMembership(id={self.pk}, user_id={self.user_id}, org_id={self.organization_id})"


class VenueRole(models.TextChoices):
    """Roles for venue membership."""

    MANAGER = "MANAGER", "Manager"
    STAFF = "STAFF", "Staff"


class VenueMembership(BaseEntity):
    """
    Links users to venues they manage or work at.

    Defines the relationship between users and venues with specific roles.
    """

    # Class constants for field lengths
    ROLE_MAX_LENGTH: int = 20

    user = models.ForeignKey(
        to=User,
        on_delete=CASCADE,
        related_name="venue_memberships",
        verbose_name="User",
        help_text="The user who is a member",
    )
    venue = models.ForeignKey(
        to=Venue,
        on_delete=CASCADE,
        related_name="memberships",
        verbose_name="Venue",
        help_text="The venue they manage",
    )
    role = models.CharField(
        max_length=ROLE_MAX_LENGTH,
        choices=VenueRole.choices,
        default=VenueRole.STAFF,
        verbose_name="Role",
        help_text="Their role at the venue (MANAGER, STAFF)",
    )

    class Meta:
        """Meta options for VenueMembership model."""

        verbose_name = "Venue Membership"
        verbose_name_plural = "Venue Memberships"
        constraints = [
            UniqueConstraint(
                fields=["user", "venue"],
                name="unique_user_venue",
            ),
        ]

    def __str__(self) -> str:
        """String representation."""
        return f"{self.user.email} - {self.venue.name} ({self.role})"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"VenueMembership(id={self.pk}, user_id={self.user_id}, venue_id={self.venue_id})"
