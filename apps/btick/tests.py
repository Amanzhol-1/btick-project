# Python modules
from datetime import timedelta
from decimal import Decimal

# Django modules
from django.contrib.auth.models import Group
from django.utils import timezone

# Django Rest Framework modules
from rest_framework import status

# Third-party modules
import pytest

# Project modules
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
from apps.btick.permissions import GROUP_CUSTOMERS


# =============================================================================
# Event Category Tests
# =============================================================================


class TestEventCategoryList:
    """Tests for event category list endpoint."""

    def test_list_categories_success(self, api_client, category):
        """Test listing categories returns data."""
        response = api_client.get("/api/v1/categories")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_categories_empty(self, api_client, db):
        """Test listing categories when none exist."""
        response = api_client.get("/api/v1/categories")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_list_categories_multiple(self, api_client, db):
        """Test listing multiple categories."""
        EventCategory.objects.create(name="Concert")
        EventCategory.objects.create(name="Workshop")
        EventCategory.objects.create(name="Conference")
        response = api_client.get("/api/v1/categories")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3


class TestEventCategoryRetrieve:
    """Tests for event category retrieve endpoint."""

    def test_retrieve_category_success(self, api_client, category):
        """Test retrieving a category by ID."""
        response = api_client.get(f"/api/v1/categories/{category.id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == category.name

    def test_retrieve_category_not_found(self, api_client, db):
        """Test retrieving non-existent category returns 404."""
        response = api_client.get("/api/v1/categories/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_category_invalid_id(self, api_client, db):
        """Test retrieving with non-existent ID returns 404."""
        response = api_client.get("/api/v1/categories/99998")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_deleted_category(self, api_client, category):
        """Test retrieving a soft-deleted category returns 404."""
        category.delete()  # Soft delete
        response = api_client.get(f"/api/v1/categories/{category.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Venue Tests
# =============================================================================


class TestVenueList:
    """Tests for venue list endpoint."""

    def test_list_venues_success(self, api_client, venue):
        """Test listing venues returns data."""
        response = api_client.get("/api/v1/venues")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_venues_empty(self, api_client, db):
        """Test listing venues when none exist."""
        response = api_client.get("/api/v1/venues")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0


class TestVenueRetrieve:
    """Tests for venue retrieve endpoint."""

    def test_retrieve_venue_success(self, api_client, venue):
        """Test retrieving a venue by ID."""
        response = api_client.get(f"/api/v1/venues/{venue.id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == venue.name

    def test_retrieve_venue_not_found(self, api_client, db):
        """Test retrieving non-existent venue returns 404."""
        response = api_client.get("/api/v1/venues/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_venue_invalid_id(self, api_client, db):
        """Test retrieving with non-existent ID returns 404."""
        response = api_client.get("/api/v1/venues/99998")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_deleted_venue(self, api_client, venue):
        """Test retrieving soft-deleted venue returns 404."""
        venue.delete()
        response = api_client.get(f"/api/v1/venues/{venue.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Organization Tests
# =============================================================================


class TestOrganizationList:
    """Tests for organization list endpoint."""

    def test_list_organizations_success(self, api_client, organization):
        """Test listing organizations returns data."""
        response = api_client.get("/api/v1/organizations")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_organizations_empty(self, api_client, db):
        """Test listing organizations when none exist."""
        response = api_client.get("/api/v1/organizations")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0


class TestOrganizationRetrieve:
    """Tests for organization retrieve endpoint."""

    def test_retrieve_organization_success(self, api_client, organization):
        """Test retrieving an organization by ID."""
        response = api_client.get(f"/api/v1/organizations/{organization.id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == organization.name

    def test_retrieve_organization_not_found(self, api_client, db):
        """Test retrieving non-existent organization returns 404."""
        response = api_client.get("/api/v1/organizations/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_organization_invalid_id(self, api_client, db):
        """Test retrieving with non-existent ID returns 404."""
        response = api_client.get("/api/v1/organizations/99998")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_deleted_organization(self, api_client, organization):
        """Test retrieving soft-deleted organization returns 404."""
        organization.delete()
        response = api_client.get(f"/api/v1/organizations/{organization.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Event Tests
# =============================================================================


class TestEventList:
    """Tests for event list endpoint."""

    def test_list_events_success(self, api_client, event):
        """Test listing published events returns data."""
        response = api_client.get("/api/v1/events")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_events_only_published(self, api_client, event, draft_event):
        """Test listing events returns only published events."""
        response = api_client.get("/api/v1/events")
        assert response.status_code == status.HTTP_200_OK
        titles = [e["title"] for e in response.data]
        assert event.title in titles
        assert draft_event.title not in titles


class TestEventRetrieve:
    """Tests for event retrieve endpoint."""

    def test_retrieve_event_success(self, api_client, event):
        """Test retrieving a published event."""
        response = api_client.get(f"/api/v1/events/{event.id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == event.title

    def test_retrieve_nonexistent_event(self, api_client, db):
        """Test retrieving non-existent event returns 404."""
        response = api_client.get("/api/v1/events/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_draft_event_public(self, api_client, draft_event):
        """Test draft events are retrievable by ID (API allows this)."""
        response = api_client.get(f"/api/v1/events/{draft_event.id}")
        # Note: The current API allows viewing any event by ID
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == draft_event.title

    def test_retrieve_event_invalid_id(self, api_client, db):
        """Test retrieving event with non-existent ID returns 404."""
        response = api_client.get("/api/v1/events/99998")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestEventCreate:
    """Tests for event create endpoint."""

    def test_create_event_unauthenticated(self, api_client, db):
        """Test creating event without authentication fails."""
        data = {"title": "Event"}
        response = api_client.post("/api/v1/events", data=data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_event_requires_permission(self, authenticated_client, organization, venue, category):
        """Test creating event requires organization membership."""
        data = {
            "title": "New Event",
            "organization": organization.id,
            "venue": venue.id,
            "category": category.id,
            "starts_at": (timezone.now() + timedelta(days=30)).isoformat(),
            "ends_at": (timezone.now() + timedelta(days=30, hours=3)).isoformat(),
        }
        response = authenticated_client.post("/api/v1/events", data=data, format="json")
        # Without organization membership, should get 403
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_event_as_organizer(self, organizer_client, organization, venue, category):
        """Test organization owner can create event."""
        data = {
            "title": "New Event by Organizer",
            "description": "Event description",
            "organization": organization.id,
            "venue": venue.id,
            "category": category.id,
            "starts_at": (timezone.now() + timedelta(days=30)).isoformat(),
            "ends_at": (timezone.now() + timedelta(days=30, hours=3)).isoformat(),
        }
        response = organizer_client.post("/api/v1/events", data=data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_event_end_before_start(self, organizer_client, organization, venue, category):
        """Test creating event with end before start fails."""
        data = {
            "title": "Invalid Event",
            "organization": organization.id,
            "venue": venue.id,
            "category": category.id,
            "starts_at": (timezone.now() + timedelta(days=30)).isoformat(),
            "ends_at": (timezone.now() + timedelta(days=29)).isoformat(),
        }
        response = organizer_client.post("/api/v1/events", data=data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# Ticket Tests
# =============================================================================


class TestTicketList:
    """Tests for ticket list endpoint."""

    def test_list_tickets_success(self, api_client, ticket):
        """Test listing tickets returns data."""
        response = api_client.get("/api/v1/tickets")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_tickets_empty(self, api_client, db):
        """Test listing tickets when none exist."""
        response = api_client.get("/api/v1/tickets")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0


class TestTicketRetrieve:
    """Tests for ticket retrieve endpoint."""

    def test_retrieve_ticket_success(self, api_client, ticket):
        """Test retrieving a ticket by ID."""
        response = api_client.get(f"/api/v1/tickets/{ticket.id}")
        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data["price"]) == ticket.price

    def test_retrieve_ticket_not_found(self, api_client, db):
        """Test retrieving non-existent ticket returns 404."""
        response = api_client.get("/api/v1/tickets/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_ticket_invalid_id(self, api_client, db):
        """Test retrieving ticket with non-existent ID returns 404."""
        response = api_client.get("/api/v1/tickets/99998")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_deleted_ticket(self, api_client, ticket):
        """Test soft-deleted ticket is still retrievable (API doesn't filter)."""
        ticket.delete()  # Soft delete
        response = api_client.get(f"/api/v1/tickets/{ticket.id}")
        # Note: Tickets API doesn't filter by is_active
        assert response.status_code == status.HTTP_200_OK


class TestTicketCreate:
    """Tests for ticket create endpoint."""

    def test_create_ticket_unauthenticated(self, api_client, event):
        """Test creating ticket without authentication fails."""
        data = {
            "event": event.id,
            "ticket_type": TicketType.STANDARD,
            "price": 50.00,
            "quota": 100,
        }
        response = api_client.post("/api/v1/tickets", data=data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_ticket_as_organizer(self, organizer_client, event):
        """Test organization owner can create ticket."""
        data = {
            "event": event.id,
            "ticket_type": TicketType.EARLY_BIRD,
            "price": "35.00",
            "quota": 50,
        }
        response = organizer_client.post("/api/v1/tickets", data=data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_ticket_requires_permission(self, authenticated_client, event):
        """Test creating ticket requires organization membership."""
        data = {
            "event": event.id,
            "ticket_type": TicketType.STANDARD,
            "price": 50.00,
            "quota": 100,
        }
        response = authenticated_client.post("/api/v1/tickets", data=data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_ticket_missing_event(self, organizer_client):
        """Test creating ticket without event fails."""
        data = {
            "ticket_type": TicketType.STANDARD,
            "price": 50.00,
            "quota": 100,
        }
        response = organizer_client.post("/api/v1/tickets", data=data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# Booking Tests
# =============================================================================


@pytest.fixture
def customer_client(api_client, user, db):
    """Return an authenticated API client for a customer user."""
    # Create the Customers group if it doesn't exist
    group, _ = Group.objects.get_or_create(name=GROUP_CUSTOMERS)
    user.groups.add(group)
    api_client.force_authenticate(user=user)
    return api_client


class TestBookingList:
    """Tests for booking list endpoint."""

    def test_list_bookings_authenticated(self, customer_client, booking):
        """Test listing own bookings."""
        response = customer_client.get("/api/v1/bookings")
        assert response.status_code == status.HTTP_200_OK

    def test_list_bookings_unauthenticated(self, api_client, db):
        """Test listing bookings without authentication fails."""
        response = api_client.get("/api/v1/bookings")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestBookingRetrieve:
    """Tests for booking retrieve endpoint."""

    def test_retrieve_booking_success(self, customer_client, booking):
        """Test retrieving own booking."""
        response = customer_client.get(f"/api/v1/bookings/{booking.id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["quantity"] == booking.quantity

    def test_retrieve_booking_unauthenticated(self, api_client, booking):
        """Test retrieving booking without authentication fails."""
        response = api_client.get(f"/api/v1/bookings/{booking.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_booking_not_found(self, customer_client, db):
        """Test retrieving non-existent booking returns 404."""
        response = customer_client.get("/api/v1/bookings/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_other_user_booking(self, api_client, booking, user2):
        """Test cannot retrieve another user's booking."""
        api_client.force_authenticate(user=user2)
        response = api_client.get(f"/api/v1/bookings/{booking.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestBookingCreate:
    """Tests for booking create endpoint."""

    def test_create_booking_success(self, customer_client, ticket):
        """Test creating a booking as customer."""
        data = {
            "event_ticket": ticket.id,
            "quantity": 2,
        }
        response = customer_client.post("/api/v1/bookings", data=data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Booking.objects.filter(event_ticket=ticket).exists()

    def test_create_booking_unauthenticated(self, api_client, ticket):
        """Test creating booking without authentication fails."""
        data = {"event_ticket": ticket.id, "quantity": 1}
        response = api_client.post("/api/v1/bookings", data=data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_booking_exceeds_quota(self, customer_client, ticket):
        """Test creating booking exceeding available tickets fails."""
        data = {"event_ticket": ticket.id, "quantity": ticket.quota + 1}
        response = customer_client.post("/api/v1/bookings", data=data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_booking_nonexistent_ticket(self, customer_client, db):
        """Test creating booking for non-existent ticket fails."""
        data = {"event_ticket": 99999, "quantity": 1}
        response = customer_client.post("/api/v1/bookings", data=data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
