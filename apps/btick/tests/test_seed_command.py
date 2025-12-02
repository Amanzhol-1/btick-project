from django.test import TestCase, override_settings
from django.core.management import call_command
from django.contrib.auth import get_user_model

from apps.btick.models import (
    Organization,
    Venue,
    EventCategory,
    Event,
    EventsTicket,
    Booking,
)

User = get_user_model()

@override_settings(DEBUG=True)
class SeedCommandHappyPathTests(TestCase):
    """
    GOOD CASE:
    We verify that with DEBUG=True and the specified parameters, 
    the seed command creates the required number of objects 
    and respects important invariants.
    """

    def test_seed_creates_requested_objects(self):
        # We call the seeder with specific parameters
        call_command(
            "seed",
            "--flush",
            "--users", "5",
            "--orgs", "2",
            "--venues", "3",
            "--cats", "4",
            "--events", "6",
            "--bookings", "10",
            "--locale", "en_US",
        )

        # 1) The number of created entities strictly corresponds to the passed parameters
        self.assertEqual(
            User.objects.filter(is_superuser=False).count(),
            5,
            msg="Exactly 5 regular users must be created",
        )
        self.assertEqual(Organization.objects.count(), 2)
        self.assertEqual(Venue.objects.count(), 3)
        self.assertEqual(EventCategory.objects.count(), 4)
        self.assertEqual(Event.objects.count(), 6)
        self.assertEqual(Booking.objects.count(), 10)

        # For each event, 2-4 ticket types are created → a total of at least 2 * 6
        self.assertGreaterEqual(
            EventsTicket.objects.count(),
            6 * 2,
            msg="Tickets must be created for each event (minimum 2 types per event)",
        )

        # 2) Booking invariant: quantity >= 2 (by CheckConstraint)
        self.assertFalse(
            Booking.objects.filter(quantity__lt=2).exists(),
            msg="All bookings must have quantity >= 2",
        )

        # 3) Invariant sold <= quota
        for ticket in EventsTicket.objects.all():
            self.assertLessEqual(
                ticket.sold,
                ticket.quota,
                msg="For each ticket, the sold field must not exceed quota",
            )


class SeedCommandEdgeCasesTests(TestCase):
    """
    BAD CASES:
    Negative scenarios and edge cases.
    """

    def test_seed_does_nothing_when_debug_false(self):
        """
        BAD CASE 1:
        If DEBUG=False, the command shouldn't create anything (protection against running the seeder in PROD/TEST).
        Here, we specifically DO NOT enable override_settings(DEBUG=True)
        to use the default DEBUG=False in tests.
        """
        call_command(
            "seed",
            "--flush",
            "--users", "3",
            "--orgs", "1",
            "--venues", "1",
            "--cats", "1",
            "--events", "1",
            "--bookings", "1",
        )

        self.assertEqual(User.objects.filter(is_superuser=False).count(), 0)
        self.assertEqual(Organization.objects.count(), 0)
        self.assertEqual(Venue.objects.count(), 0)
        self.assertEqual(EventCategory.objects.count(), 0)
        self.assertEqual(Event.objects.count(), 0)
        self.assertEqual(EventsTicket.objects.count(), 0)
        self.assertEqual(Booking.objects.count(), 0)

    @override_settings(DEBUG=True)
    def test_seed_flush_replaces_old_data(self):
        """
        BAD CASE 2 (edge case):
        We check that --flush deletes old data and creates new ones.
        """
        # We pre-create "old" data
        old_user = User.objects.create(email="old@example.com")
        Organization.objects.create(name="Old Org")
        Venue.objects.create(name="Old Venue")
        EventCategory.objects.create(name="Old Category")

        # Run the seeder with the --flush flag.
        call_command(
            "seed",
            "--flush",
            "--users", "5",
            "--orgs", "2",
            "--venues", "3",
            "--cats", "4",
            "--events", "5",
            "--bookings", "5",
        )

        # The old user must be deleted.
        self.assertFalse(User.objects.filter(pk=old_user.pk).exists())

        # New data must strictly comply with the parameters
        self.assertEqual(User.objects.filter(is_superuser=False).count(), 5)
        self.assertEqual(Organization.objects.count(), 2)
        self.assertEqual(Venue.objects.count(), 3)
        self.assertEqual(EventCategory.objects.count(), 4)

        @override_settings(DEBUG=True)
        def test_seed_without_flush_keeps_old_users(self):
            """
            BAD CASE 3 (edge case):
            Without --flush , old users should remain, and the seeder simply adds new ones.
            """
            # Two existing users with different usernames,
            # to avoid violating the UNIQUE constraint.
            User.objects.create(username="old1", email="old1@example.com")
            User.objects.create(username="old2", email="old2@example.com")

            # Run the seeder WITHOUT --flush
            call_command(
                "seed",
                "--users", "3",
                "--orgs", "1",
                "--venues", "1",
                "--cats", "1",
                "--events", "1",
                "--bookings", "1",
            )

            # Total: 2 old + 3 new = 5 regular users
            self.assertEqual(
                User.objects.filter(is_superuser=False).count(),
                5,
                msg="Without --flush the seeder should add users instead of deleting old ones.",
            )

