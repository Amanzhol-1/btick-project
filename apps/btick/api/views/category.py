from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.btick.models import EventCategory
from apps.btick.api.serializers import EventCategorySerializer


class EventCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for EventCategory model

    Provides read-only access to event categories
    Used for filtering events by category type
    """

    queryset = EventCategory.objects.filter(is_active=True).order_by('name')
    serializer_class = EventCategorySerializer
    permission_classes = [AllowAny]