from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.btick.models import Venue
from apps.btick.api.serializers import VenueSerializer


class VenueViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Venue

    Provides read-only access to Venue information.
    Users can view venue details to see where events are held
    """

    queryset = Venue.objects.filter(is_active=True).order_by('name')
    serializer_class = VenueSerializer
    permission_classes = [AllowAny]