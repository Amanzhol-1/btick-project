from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.btick.views import (
    EventViewSet,
    EventCategoryViewSet,
    VenueViewSet,
    OrganizationViewSet,
    BookingViewSet,
    TicketViewSet,
)

router = DefaultRouter()

router.register(r'events', EventViewSet, basename='event')
router.register(r'categories', EventCategoryViewSet, basename='category')
router.register(r'venues', VenueViewSet, basename='venue')
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'tickets', TicketViewSet, basename='ticket')

app_name = 'btick'

urlpatterns = [
    path('', include(router.urls)),
]
