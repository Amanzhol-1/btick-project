from __future__ import annotations

import random
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum

from faker import Faker

from apps.btick.models import (
    Organization,
    Venue,
    EventCategory,
    Event,
    EventsTicket,
    Booking,
    EventStatus,
    BookingStatus,
)

"""
Management command for populating the local database with test data
for the BTick project (users, organizations, venues, events,
ticket and booking types).
"""

User = get_user_model()


def _ticket_codes_from_model() -> list[str]:
    """
    We take the codes from the EventsTicket.ticket_type field's choices 
    so as not to depend on the existence of a separate TicketType class.
    """
    field = EventsTicket._meta.get_field("ticket_type")
    choices = getattr(field, "choices", None) or []
    codes = [code for code, _ in choices]
    # a backup list in case the choices are suddenly empty
    return codes or ["STANDARD", "VIP", "EARLY_BIRD", "STUDENT", "GROUP"]


class Command(BaseCommand):
    """
    Django management command `seed`, which generates 
    test data for local development and testing.
    """

    help = "Seed DEV database with sample data for btick."

    def add_arguments(self, parser):
        """
        Description of the command's CLI arguments 
        (number of users, events, bookings, and the --flush flag for clearing the database before generation).
        """
        parser.add_argument("--users", type=int, default=15, help="Количество пользователей")
        parser.add_argument("--orgs", type=int, default=4, help="Количество организаций")
        parser.add_argument("--venues", type=int, default=5, help="Количество площадок")
        parser.add_argument("--cats", type=int, default=6, help="Количество категорий событий")
        parser.add_argument("--events", type=int, default=10, help="Количество событий")
        parser.add_argument("--bookings", type=int, default=60, help="Количество бронирований")
        parser.add_argument("--flush", action="store_true", help="Очистить существующие данные перед засевом")
        parser.add_argument("--locale", type=str, default="ru_RU", help="Локаль Faker (ru_RU/en_US/...)")

    @transaction.atomic
    def handle(self, *args, **opts):
        """
        The basic logic of the command:
        - with --flush, we clear the data step by step,
        - create users, organizations, venues, event categories,
        events, tickets, and bookings,
        - recalculate the "sold" field for tickets.
        Everything is done in a single transaction.
        """
        if not getattr(settings, "DEBUG", True):
            self.stderr.write(self.style.ERROR("DEBUG=False — The seeder is intended only for DEVs."))
            return

        fake = Faker(opts["locale"])

        users_n = int(opts["users"])
        orgs_n = int(opts["orgs"])
        venues_n = int(opts["venues"])
        cats_n = int(opts["cats"])
        events_n = int(opts["events"])
        bookings_n = int(opts["bookings"])
        do_flush = bool(opts["flush"])

        if do_flush:
            self._flush_all()

        users = self._seed_users(fake, users_n)
        orgs = self._seed_orgs(fake, orgs_n)
        venues = self._seed_venues(fake, venues_n)
        cats = self._seed_categories(fake, cats_n)
        events = self._seed_events(fake, events_n, orgs, venues, cats)
        tickets = self._seed_event_tickets(events)
        bookings = self._seed_bookings(fake, bookings_n, users, tickets)

        self._recount_sold_per_ticket()

        self.stdout.write(self.style.SUCCESS(
            "Seed complete ✔\n"
            f"  Users: {len(users)}\n"
            f"  Orgs: {len(orgs)} | Venues: {len(venues)} | Categories: {len(cats)}\n"
            f"  Events: {len(events)} | Tickets: {len(tickets)}\n"
            f"  Bookings: {len(bookings)}"
        ))

    # ---------- helpers ----------

    def _flush_all(self):
        """
        Completely clear domain model data (but do not touch superusers).
        """
        self.stdout.write(self.style.WARNING("Flushing old data..."))
        Booking.objects.all().delete()
        EventsTicket.objects.all().delete()
        Event.objects.all().delete()
        EventCategory.objects.all().delete()
        Venue.objects.all().delete()
        Organization.objects.all().delete()
        # don't touch the admins
        User.objects.exclude(is_superuser=True).delete()

    def _seed_users(self, fake: Faker, n: int):
        """
        Generate n users.
        Default password: password123
        """
        created = []
        for _ in range(n):
            email = fake.unique.email()
            u = User(email=email)
            if hasattr(u, "username"):
                u.username = email.split("@")[0]
            u.set_password("password123")
            u.save()
            created.append(u)
        return created

    def _seed_orgs(self, fake: Faker, n: int):
        """
        Generation of organizing organizations.
        """
        objs = []
        for _ in range(n):
            objs.append(Organization(
                name=fake.unique.company(),
                website=fake.url(),
                contact_email=fake.unique.company_email(),
            ))
        Organization.objects.bulk_create(objs)
        return list(Organization.objects.order_by("-id")[:n])

    def _seed_venues(self, fake: Faker, n: int):
        """
        Generation of venues for events.
        """
        objs = []
        for _ in range(n):
            objs.append(Venue(
                name=fake.unique.company() + " Hall",
                address=fake.address().replace("\n", ", "),
                capacity=random.randint(100, 5000),
            ))
        Venue.objects.bulk_create(objs)
        return list(Venue.objects.order_by("-id")[:n])

    def _seed_categories(self, fake: Faker, n: int):
        """
        Generation of event categories (Music, IT, Sport...).
        """
        seen = set()
        objs = []
        while len(objs) < n:
            name = fake.word().title()
            if name in seen:
                name = f"{name} {len(objs) + 1}"
            seen.add(name)
            objs.append(EventCategory(name=name))
        EventCategory.objects.bulk_create(objs)
        return list(EventCategory.objects.order_by("-id")[:n])

    def _seed_events(self, fake: Faker, n: int, orgs, venues, cats):
        """
        Event generation: binding to organizer, venue, and category.
        Maintaining the ends_at > starts_at invariant.
        """
        tz = timezone.get_current_timezone()
        objs = []
        for _ in range(n):
            start = fake.date_time_between(start_date="+2d", end_date="+90d", tzinfo=tz)
            end = start + timezone.timedelta(hours=random.choice([2, 3, 4]))
            objs.append(Event(
                organization=random.choice(orgs),
                venue=random.choice(venues),
                category=random.choice(cats),
                title=fake.unique.catch_phrase(),
                description=fake.paragraph(nb_sentences=3),
                starts_at=start,
                ends_at=end,
                status=random.choice([EventStatus.DRAFT, EventStatus.PUBLISHED]),
                capacity=random.choice([None, random.randint(100, 5000)]),
            ))
        Event.objects.bulk_create(objs)
        return list(Event.objects.order_by("-id")[:n])

    def _seed_event_tickets(self, events):
        """
        For each event, we create 2–4 ticket types (unique by (event, ticket_type)).
        """
        all_types = _ticket_codes_from_model()

        price_map = {
            "STANDARD": Decimal("5990.00"),
            "VIP": Decimal("15990.00"),
            "EARLY_BIRD": Decimal("3990.00"),
            "STUDENT": Decimal("2990.00"),
            "GROUP": Decimal("4990.00"),
        }

        to_create = []
        for event in events:
            k = min(max(2, random.randint(2, 4)), len(all_types))
            types_for_event = random.sample(all_types, k=k)
            for tt in types_for_event:
                to_create.append(EventsTicket(
                    event=event,
                    ticket_type=tt,
                    price=price_map.get(tt, Decimal("5990.00")),
                    quota=random.randint(50, 500),
                    sold=0,  # We will recalculate after bookings
                ))
        EventsTicket.objects.bulk_create(to_create)
        return list(EventsTicket.objects.filter(event__in=events))

    def _seed_bookings(self, fake: Faker, n: int, users, tickets):
        """
        Generating bookings:
        - quantity >= 2 (validate CheckConstraint),
        - for PENDING, set expires_at 1 day before the event.
        """
        if not tickets:
            return []

        tz = timezone.get_current_timezone()
        to_create = []
        for _ in range(n):
            ticket = random.choice(tickets)
            user = random.choice(users)
            qty = random.randint(2, 5)  # >= 2 — important for your CheckConstraint

            status = random.choices(
                population=[BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.CANCELLED],
                weights=[0.25, 0.65, 0.10],
                k=1
            )[0]

            expires = None
            if status == BookingStatus.PENDING:
                expires = (ticket.event.starts_at - timezone.timedelta(days=1)).astimezone(tz)

            to_create.append(Booking(
                user=user,
                event_ticket=ticket,
                quantity=qty,
                status=status,
                expires_at=expires,
            ))
        Booking.objects.bulk_create(to_create)
        return list(Booking.objects.order_by("-id")[:n])

    def _recount_sold_per_ticket(self):
        """
        sold = the amount of quantity for CONFIRMED bookings, but not more than quota.
        """
        confirmed = (
            Booking.objects
            .filter(status=BookingStatus.CONFIRMED)
            .values("event_ticket_id")
            .annotate(total_qty=Sum("quantity"))
        )
        totals = {row["event_ticket_id"]: (row["total_qty"] or 0) for row in confirmed}

        tickets = list(EventsTicket.objects.all())
        for t in tickets:
            t.sold = min(totals.get(t.id, 0), t.quota)
        if tickets:
            EventsTicket.objects.bulk_update(tickets, ["sold"])
