# Django modules
from django.urls import path, include

# Django Rest Framework modules
from rest_framework.routers import DefaultRouter

# Project modules
from apps.btick.views import (
    EventViewSet,
    EventCategoryViewSet,
    VenueViewSet,
    OrganizationViewSet,
    BookingViewSet,
    TicketViewSet,
)


router: DefaultRouter = DefaultRouter(trailing_slash=False)

router.register(
    prefix="events",
    viewset=EventViewSet,
    basename="event",
)
router.register(
    prefix="categories",
    viewset=EventCategoryViewSet,
    basename="category",
)
router.register(
    prefix="venues",
    viewset=VenueViewSet,
    basename="venue",
)
router.register(
    prefix="organizations",
    viewset=OrganizationViewSet,
    basename="organization",
)
router.register(
    prefix="bookings",
    viewset=BookingViewSet,
    basename="booking",
)
router.register(
    prefix="tickets",
    viewset=TicketViewSet,
    basename="ticket",
)

app_name: str = "btick"

urlpatterns: list = [
    path("", include(router.urls)),
]
