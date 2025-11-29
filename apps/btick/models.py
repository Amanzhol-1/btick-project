from django.db import models
from django.db.models import PROTECT, CheckConstraint, Q, F, UniqueConstraint, CASCADE
from django.conf import settings
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

from apps.abstracts.models import BaseEntity

User = get_user_model()

class EventStatus(models.TextChoices):
    DRAFT = 'DRAFT'
    PUBLISHED = 'PUBLISHED'
    CANCELLED = 'CANCELLED'


class BookingStatus(models.TextChoices):
    PENDING = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    CANCELLED = 'CANCELLED'


class TicketType(models.TextChoices):
    STANDARD = 'STANDARD', 'Standard'
    VIP = 'VIP', 'VIP'
    EARLY_BIRD = 'EARLY_BIRD', 'Early Bird'
    STUDENT = 'STUDENT', 'Student'
    GROUP = 'GROUP', 'Group'


class Organization(BaseEntity):
    """
    TODO: Add docs strings
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

    """
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        verbose_name = 'Event Category'
        verbose_name_plural = 'Event Categories'

    def __str__(self):
        return self.name


class Event(BaseEntity):
    """

    """
    organization = models.ForeignKey(Organization, on_delete=PROTECT, related_name='events')
    venue = models.ForeignKey(Venue, on_delete=PROTECT, related_name='events')
    category = models.ForeignKey(EventCategory, on_delete=PROTECT, related_name='events')
    title = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=12, choices=EventStatus.choices, default=EventStatus.DRAFT)
    capacity = models.PositiveIntegerField(null = True, blank= True)

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
