from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.btick.models import Organization
from apps.btick.api.serializers import OrganizationSerializer


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Organization model

    Provides read-only access to event organizer information.
    Users can view organization details to learn about event hosts
    """

    queryset = Organization.objects.filter(is_active=True).order_by('name')
    serializer_class = OrganizationSerializer
    permission_classes = [AllowAny]