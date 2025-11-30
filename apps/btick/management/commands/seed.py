# apps/btick/management/commands/seed.py
from __future__ import annotations

import random
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction, models
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
    OrganizationMembership,
    VenueMembership,
    OrganizationRole,
    VenueRole,
)

User = get_user_model()


def _ticket_codes_from_model() -> list[str]:
    """
    Берём коды из choices поля EventsTicket.ticket_type, чтобы не зависеть
    от наличия отдельно объявленного класса TicketType.
    """
    field = EventsTicket._meta.get_field("ticket_type")
    choices = getattr(field, "choices", None) or []
    codes = [code for code, _ in choices]
    # запасной список на случай пустых choices
    return codes or ["STANDARD", "VIP", "EARLY_BIRD", "STUDENT", "GROUP"]


class Command(BaseCommand):
    help = "Seed DEV database with sample data for btick."

    def add_arguments(self, parser):
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
        # Защита от запуска в проде
        if not getattr(settings, "DEBUG", True):
            self.stderr.write(self.style.ERROR("DEBUG=False — сидер предназначен только для DEV."))
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

        # Create memberships and assign groups
        org_memberships = self._seed_org_memberships(users, orgs)
        venue_memberships = self._seed_venue_memberships(users, venues)
        self._assign_groups(users, org_memberships, venue_memberships)

        self._recount_sold_per_ticket()

        self.stdout.write(self.style.SUCCESS(
            "Seed complete ✔\n"
            f"  Users: {len(users)}\n"
            f"  Orgs: {len(orgs)} | Venues: {len(venues)} | Categories: {len(cats)}\n"
            f"  Events: {len(events)} | Tickets: {len(tickets)}\n"
            f"  Bookings: {len(bookings)}\n"
            f"  Org Memberships: {len(org_memberships)} | Venue Memberships: {len(venue_memberships)}"
        ))

    # ---------- helpers ----------

    def _flush_all(self):
        self.stdout.write(self.style.WARNING("Flushing old data..."))
        # Flush memberships first (depend on users, orgs, venues)
        OrganizationMembership.objects.all().hard_delete()
        VenueMembership.objects.all().hard_delete()
        Booking.objects.all().hard_delete()
        EventsTicket.objects.all().hard_delete()
        Event.objects.all().hard_delete()
        EventCategory.objects.all().hard_delete()
        Venue.objects.all().hard_delete()
        Organization.objects.all().hard_delete()
        # Don't touch superusers
        User.objects.exclude(is_superuser=True).delete()

    def _seed_users(self, fake: Faker, n: int):
        created = []
        for _ in range(n):
            email = fake.unique.email()
            u = User(email=email)
            # Populate profile fields
            u.first_name = fake.first_name()
            u.last_name = fake.last_name()
            u.phone = fake.phone_number()[:20]  # Limit to field max_length
            if hasattr(u, "bio"):
                u.bio = fake.sentence(nb_words=10)
            # Handle legacy username field if exists
            if hasattr(u, "username"):
                u.username = email.split("@")[0]
            u.set_password("password123")
            u.save()
            created.append(u)
        return created

    def _seed_orgs(self, fake: Faker, n: int):
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
        seen = set()
        objs = []
        while len(objs) < n:
            name = fake.word().title()
            if name in seen:
                name = f"{name} {len(objs)+1}"
            seen.add(name)
            objs.append(EventCategory(name=name))
        EventCategory.objects.bulk_create(objs)
        return list(EventCategory.objects.order_by("-id")[:n])

    def _seed_events(self, fake: Faker, n: int, orgs, venues, cats):
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
                ends_at=end,  # соблюдаем constraint ends_at > starts_at
                status=random.choice([EventStatus.DRAFT, EventStatus.PUBLISHED]),
                capacity=random.choice([None, random.randint(100, 5000)]),
            ))
        Event.objects.bulk_create(objs)
        return list(Event.objects.order_by("-id")[:n])

    def _seed_event_tickets(self, events):
        """
        Для каждого события создаём 2–4 типа билетов (уникально по (event, ticket_type)).
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
                    sold=0,  # пересчитаем после бронирований
                ))
        EventsTicket.objects.bulk_create(to_create)
        return list(EventsTicket.objects.filter(event__in=events))

    def _seed_bookings(self, fake: Faker, n: int, users, tickets):
        """
        Booking.quantity >= 2 (ваш CheckConstraint).
        Для PENDING выставляем expires_at за 1 день до начала события.
        """
        if not tickets:
            return []

        tz = timezone.get_current_timezone()
        to_create = []
        for _ in range(n):
            ticket = random.choice(tickets)
            user = random.choice(users)
            qty = random.randint(2, 5)  # >= 2 — важно!

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
        sold = сумма quantity по CONFIRMED-бронированиям, ограничиваем sold <= quota.
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

    def _seed_org_memberships(self, users: list, orgs: list) -> list:
        """
        Assign users to organizations with different roles.
        Each org gets 1 OWNER and 1-2 MANAGERS from the user pool.
        """
        if not users or not orgs:
            return []

        memberships = []
        available_users = list(users)
        random.shuffle(available_users)

        for org in orgs:
            # Assign an owner
            if available_users:
                owner = available_users.pop(0)
                memberships.append(OrganizationMembership(
                    user=owner,
                    organization=org,
                    role=OrganizationRole.OWNER,
                ))

            # Assign 1-2 managers
            num_managers = min(random.randint(1, 2), len(available_users))
            for _ in range(num_managers):
                if available_users:
                    manager = available_users.pop(0)
                    memberships.append(OrganizationMembership(
                        user=manager,
                        organization=org,
                        role=OrganizationRole.MANAGER,
                    ))

        OrganizationMembership.objects.bulk_create(memberships)
        return memberships

    def _seed_venue_memberships(self, users: list, venues: list) -> list:
        """
        Assign users as venue managers.
        Each venue gets 1 MANAGER from the user pool.
        """
        if not users or not venues:
            return []

        memberships = []
        # Use users who aren't already org owners/managers
        org_user_ids = set(
            OrganizationMembership.objects.values_list('user_id', flat=True)
        )
        available_users = [u for u in users if u.id not in org_user_ids]

        if not available_users:
            # Fall back to all users if needed
            available_users = list(users)

        random.shuffle(available_users)

        for venue in venues:
            if available_users:
                manager = available_users.pop(0)
                memberships.append(VenueMembership(
                    user=manager,
                    venue=venue,
                    role=VenueRole.MANAGER,
                ))

        VenueMembership.objects.bulk_create(memberships)
        return memberships

    def _assign_groups(self, users: list, org_memberships: list, venue_memberships: list):
        """
        Assign users to permission groups based on their roles.
        - All non-staff users -> Customers
        - Org owners/managers -> Organizers
        - Venue managers -> Venue Managers
        """
        # Get or skip if groups don't exist
        try:
            customers_group = Group.objects.get(name='Customers')
            organizers_group = Group.objects.get(name='Organizers')
            venue_managers_group = Group.objects.get(name='Venue Managers')
        except Group.DoesNotExist:
            self.stdout.write(self.style.WARNING(
                "Permission groups not found. Run 'python manage.py setup_groups' first."
            ))
            return

        # Get user IDs by role
        org_user_ids = set(m.user_id for m in org_memberships)
        venue_user_ids = set(m.user_id for m in venue_memberships)

        for user in users:
            # All users are customers
            user.groups.add(customers_group)

            # Org members also get Organizers group
            if user.id in org_user_ids:
                user.groups.add(organizers_group)

            # Venue managers also get Venue Managers group
            if user.id in venue_user_ids:
                user.groups.add(venue_managers_group)

        self.stdout.write(f"  Assigned groups: {len(users)} customers, "
                         f"{len(org_user_ids)} organizers, {len(venue_user_ids)} venue managers")
