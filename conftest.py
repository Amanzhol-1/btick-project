# Python modules
from datetime import timedelta

# Django modules
from django.contrib.auth.models import Group
from django.utils import timezone

# Django Rest Framework modules
from rest_framework.test import APIClient

# Third-party modules
import pytest

# Project modules
from apps.accounts.models import User
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
    TicketType,
    Venue,
)
from apps.btick.permissions import GROUP_ORGANIZERS


# =============================================================================
# Base Fixtures
# =============================================================================


@pytest.fixture
def api_client() -> APIClient:
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def user(db) -> User:
    """Create and return a test user."""
    return User.objects.create_user(
        email="test@example.com",
        password="SecurePass123!",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def user2(db) -> User:
    """Create and return a second test user."""
    return User.objects.create_user(
        email="user2@example.com",
        password="SecurePass123!",
        first_name="Second",
        last_name="User",
    )


@pytest.fixture
def authenticated_client(api_client: APIClient, user: User) -> APIClient:
    """Return an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


# =============================================================================
# BTick Model Fixtures
# =============================================================================


@pytest.fixture
def organization(db) -> Organization:
    """Create and return a test organization."""
    return Organization.objects.create(
        name="Test Organization",
        website="https://test.org",
        contact_email="contact@test.org",
    )


@pytest.fixture
def venue(db) -> Venue:
    """Create and return a test venue."""
    return Venue.objects.create(
        name="Test Venue",
        address="123 Test Street",
        capacity=1000,
    )


@pytest.fixture
def category(db) -> EventCategory:
    """Create and return a test event category."""
    return EventCategory.objects.create(
        name="Concert",
    )


@pytest.fixture
def event(db, organization: Organization, venue: Venue, category: EventCategory) -> Event:
    """Create and return a test event."""
    return Event.objects.create(
        organization=organization,
        venue=venue,
        category=category,
        title="Test Event",
        description="A test event description",
        starts_at=timezone.now() + timedelta(days=7),
        ends_at=timezone.now() + timedelta(days=7, hours=3),
        status=EventStatus.PUBLISHED,
        capacity=500,
    )


@pytest.fixture
def draft_event(db, organization: Organization, venue: Venue, category: EventCategory) -> Event:
    """Create and return a draft event."""
    return Event.objects.create(
        organization=organization,
        venue=venue,
        category=category,
        title="Draft Event",
        description="A draft event",
        starts_at=timezone.now() + timedelta(days=14),
        ends_at=timezone.now() + timedelta(days=14, hours=2),
        status=EventStatus.DRAFT,
    )


@pytest.fixture
def ticket(db, event: Event) -> EventsTicket:
    """Create and return a test ticket."""
    return EventsTicket.objects.create(
        event=event,
        ticket_type=TicketType.STANDARD,
        price=50.00,
        quota=100,
        sold=0,
    )


@pytest.fixture
def vip_ticket(db, event: Event) -> EventsTicket:
    """Create and return a VIP ticket."""
    return EventsTicket.objects.create(
        event=event,
        ticket_type=TicketType.VIP,
        price=150.00,
        quota=50,
        sold=0,
    )


@pytest.fixture
def booking(db, user: User, ticket: EventsTicket) -> Booking:
    """Create and return a test booking."""
    return Booking.objects.create(
        user=user,
        event_ticket=ticket,
        quantity=2,
        status=BookingStatus.PENDING,
        expires_at=timezone.now() + timedelta(minutes=15),
    )


@pytest.fixture
def confirmed_booking(db, user: User, ticket: EventsTicket) -> Booking:
    """Create and return a confirmed booking."""
    return Booking.objects.create(
        user=user,
        event_ticket=ticket,
        quantity=1,
        status=BookingStatus.CONFIRMED,
    )


@pytest.fixture
def organization_owner(db, user: User, organization: Organization) -> OrganizationMembership:
    """Create an organization owner membership."""
    return OrganizationMembership.objects.create(
        user=user,
        organization=organization,
        role=OrganizationRole.OWNER,
    )


@pytest.fixture
def organizer_client(
    api_client: APIClient,
    user: User,
    organization_owner: OrganizationMembership,
    db,
) -> APIClient:
    """Return an authenticated API client for an organization owner."""
    # Add user to Organizers group for permission checks
    group, _ = Group.objects.get_or_create(name=GROUP_ORGANIZERS)
    user.groups.add(group)
    api_client.force_authenticate(user=user)
    return api_client
