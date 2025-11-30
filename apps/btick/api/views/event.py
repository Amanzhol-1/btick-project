from django.db import models
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.btick.models import Event
from apps.btick.api.serializers import (
    EventListSerializer,
    EventDetailSerializer,
    TicketListSerializer,
)
from apps.btick.api.filters.event import EventFilter


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Event model.

    Provides read-only access to published events with filtering capabilities.
    Users can browse events, view details, and check ticket availability.
    """

    queryset = Event.objects.filter(
        status='PUBLISHED',
        is_active=True,
        ends_at__gt=timezone.now()
    ).select_related(
        'organization',
        'venue',
        'category'
    ).order_by('starts_at')

    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EventFilter
    search_fields = ['title', 'description']
    ordering_fields = ['starts_at', 'created_at', 'title']
    ordering = ['starts_at']  # Default ordering

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.

        Returns:
            Serializer class for current action.
        """
        if self.action == 'retrieve':
            return EventDetailSerializer
        return EventListSerializer

    def get_queryset(self):
        """
        Optimize queryset based on action.

        For detail view, prefetch tickets to avoid N+1 queries.

        Returns:
            Optimized queryset.
        """
        queryset = super().get_queryset()

        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('tickets')

        return queryset

    @action(detail=True, methods=['get'], url_path='available-tickets')
    def available_tickets(self, request, pk=None):
        """
        Get available ticket tiers for a specific event.

        Returns only tickets that have availability (quota > sold).
        Useful for booking interface to show only purchasable tickets.

        Args:
            request: HTTP request object.
            pk: Event primary key.

        Returns:
            Response: List of available tickets with pricing and availability.
        """
        event = self.get_object()

        # Get tickets with available inventory
        available_tickets = event.tickets.filter(
            quota__gt=models.F('sold')
        ).order_by('price')

        serializer = TicketListSerializer(available_tickets, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)