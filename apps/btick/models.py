from django.db import models
from django.db.models import PROTECT, CheckConstraint, Q, F, UniqueConstraint, CASCADE
from django.conf import settings
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

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
    DRAFT = 'DRAFT'
    PUBLISHED = 'PUBLISHED'
    CANCELLED = 'CANCELLED'


class BookingStatus(models.TextChoices):
    """
    Enum representing the status of a ticket Booking.

    Values:
        PENDING: Booking created but not yet confirmed (awaiting payment).
        CONFIRMED: Booking is confirmed and tickets are reserved.
        CANCELLED: Booking has been cancelled.
    """
    PENDING = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    CANCELLED = 'CANCELLED'


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
    STANDARD = 'STANDARD', 'Standard'
    VIP = 'VIP', 'VIP'
    EARLY_BIRD = 'EARLY_BIRD', 'Early Bird'
    STUDENT = 'STUDENT', 'Student'
    GROUP = 'GROUP', 'Group'


class Organization(BaseEntity):
    """
    Represents an event organizer or company that hosts events.

    Organizations are the top-level entities that create and manage events.
    They can have multiple events associated with them.

    Attributes:
        name: Unique name of the organization.
        website: Optional URL to the organization's website.
        contact_email: Optional email address for inquiries.

    Relationships:
        events: One-to-many relationship with Event model.
    """
    name = models.CharField(max_length=200, unique=True)
    website = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)

    class Meta:
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def __str__(self):
        return self.name


class Venue(BaseEntity):
    """
    Represents a physical location where events are held.

    Venues define the location and maximum capacity for events.
    Multiple events can be scheduled at the same venue.

    Attributes:
        name: Unique name of the venue.
        address: Optional physical address of the venue.
        capacity: Maximum number of attendees the venue can hold.

    Relationships:
        events: One-to-many relationship with Event model.
    """
    name = models.CharField(max_length=200, unique=True)
    address = models.CharField(max_length=500, blank=True)
    capacity = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Venue'
        verbose_name_plural = 'Venues'

    def __str__(self):
        return self.name


class EventCategory(BaseEntity):
    """
    Represents a classification category for events.

    Categories help organize and filter events by type
    (e.g., Concert, Conference, Workshop, Sports).

    Attributes:
        name: Unique name of the category.

    Relationships:
        events: One-to-many relationship with Event model.
    """
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        verbose_name = 'Event Category'
        verbose_name_plural = 'Event Categories'

    def __str__(self):
        return self.name


class Event(BaseEntity):
    """
    Represents a scheduled event that users can book tickets for.

    Events are the core entity of the ticketing system. Each event belongs
    to an organization, takes place at a venue, and has a category.

    Attributes:
        organization: The organization hosting this event.
        venue: The location where the event takes place.
        category: The type/category of the event.
        title: Unique title of the event.
        description: Optional detailed description of the event.
        starts_at: Date and time when the event begins.
        ends_at: Date and time when the event ends.
        status: Current lifecycle status (DRAFT, PUBLISHED, CANCELLED).
        capacity: Optional override for venue capacity for this event.

    Relationships:
        tickets: One-to-many relationship with EventsTicket model.

    Constraints:
        - ends_at must be greater than starts_at.
    """
    organization = models.ForeignKey(Organization, on_delete=PROTECT, related_name='events')
    venue = models.ForeignKey(Venue, on_delete=PROTECT, related_name='events')
    category = models.ForeignKey(EventCategory, on_delete=PROTECT, related_name='events')
    title = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=12, choices=EventStatus.choices, default=EventStatus.DRAFT)
    capacity = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
        constraints = [
            CheckConstraint(check=Q(ends_at__gt=F("starts_at")), name = "event_ends_after_start")
        ]

    def __str__(self):
        return self.title


class EventsTicket(BaseEntity):
    """
    Represents a ticket tier available for purchase for an event.

    Each event can have multiple ticket types (e.g., Standard, VIP)
    with different prices and quotas. Tracks inventory via quota and sold.

    Attributes:
        event: The event this ticket belongs to.
        ticket_type: The tier of the ticket (STANDARD, VIP, etc.).
        price: Price per ticket in the default currency.
        quota: Total number of tickets available for sale.
        sold: Number of tickets already sold.

    Relationships:
        bookings: One-to-many relationship with Booking model.

    Constraints:
        - Unique combination of event and ticket_type.
        - price must be non-negative.
        - quota must be non-negative.
        - sold must be non-negative.
    """
    event = models.ForeignKey(Event, on_delete=CASCADE, related_name='tickets')
    ticket_type = models.CharField(max_length=80, choices=TicketType.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quota = models.PositiveIntegerField(default=0)
    sold = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Events Ticket'
        verbose_name_plural = 'Events Tickets'
        constraints = [
            UniqueConstraint(fields=["event", "ticket_type"], name="event_ticket_type_unique"),
            CheckConstraint(check=Q(price__gte=0), name="ticker_price_non_negative"),
            CheckConstraint(check=Q(quota__gte=0), name="quota_non_negative"),
            CheckConstraint(check=Q(sold__gte=0), name="sold_non_negative"),
        ]

    def __str__(self):
        return self.ticket_type


class Booking(BaseEntity):
    """
    Represents a user's ticket reservation for an event.

    Bookings link users to event tickets and track the purchase status.
    A booking can be pending (awaiting payment), confirmed, or cancelled.

    Attributes:
        user: The user who made the booking.
        event_ticket: The specific ticket type being booked.
        quantity: Number of tickets in this booking.
        status: Current status (PENDING, CONFIRMED, CANCELLED).
        expires_at: Optional expiration time for pending bookings.

    Constraints:
        - quantity must be greater than 1.
    """
    user = models.ForeignKey(User, on_delete=CASCADE, related_name='bookings')
    event_ticket = models.ForeignKey(EventsTicket, on_delete=PROTECT, related_name='bookings')
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=12, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        constraints = [
            CheckConstraint(check=Q(quantity__gt=1), name="booking_quantity_ge_1"),
        ]

    def __str__(self):
        return f"Booking {self.pk}> {self.user_id} x{self.quantity} {self.event_ticket.ticket_type}"
