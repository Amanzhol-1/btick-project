from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.btick.api.views import (
    EventViewSet,
    EventCategoryViewSet,
    VenueViewSet,
    OrganizationViewSet,
    BookingViewSet
)

router = DefaultRouter()

router.register(r'events', EventViewSet, basename='event')
router.register(r'categories', EventCategoryViewSet, basename='category')
router.register(r'venues', VenueViewSet, basename='venue')
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'bookings', BookingViewSet, basename='booking')

app_name = 'btick'

urlpatterns = [
    path('', include(router.urls)),
]