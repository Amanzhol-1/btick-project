from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.btick.models import Booking, BookingStatus
from apps.btick.api.serializers import (
    BookingListSerializer,
    BookingDetailSerializer,
    BookingCreateSerializer,
    BookingCancelSerializer,
    BookingConfirmSerializer,
)


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Booking model.

    Handles complete booking lifecycle: creation, viewing, cancellation, confirmation.
    Users can only view and manage their own bookings.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter bookings to show only current user's bookings.

        Returns:
            Queryset: User's bookings with optimized joins.
        """
        return Booking.objects.filter(
            user=self.request.user
        ).select_related(
            'event_ticket',
            'event_ticket__event',
            'event_ticket__event__venue',
            'event_ticket__event__organization',
            'event_ticket__event__category'
        ).order_by('-created_at')

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.

        Returns:
            Serializer class for current action.
        """
        if self.action == 'create':
            return BookingCreateSerializer
        elif self.action == 'retrieve':
            return BookingDetailSerializer
        elif self.action == 'cancel':
            return BookingCancelSerializer
        elif self.action == 'confirm':
            return BookingConfirmSerializer
        return BookingListSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new booking.

        Validates ticket availability and event status.
        Atomically reserves tickets and creates booking.

        Args:
            request: HTTP request with event_ticket and quantity.

        Returns:
            Response: Created booking details with 201 status.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()

        output_serializer = BookingDetailSerializer(booking)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['patch'], url_path='cancel')
    def cancel(self, request, pk=None):
        """
        Cancel a booking and return tickets to inventory.

        Only PENDING or CONFIRMED bookings can be cancelled.
        Cannot cancel bookings for events that have already started.
        Atomically returns tickets to available inventory.

        Args:
            request: HTTP request object.
            pk: Booking primary key.

        Returns:
            Response: Cancellation confirmation with updated booking.
        """
        booking = self.get_object()
        serializer = self.get_serializer(booking, data={})
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()

        output_serializer = BookingDetailSerializer(updated_booking)
        return Response({
            'message': 'Booking cancelled successfully.',
            'booking': output_serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        """
        Confirm a pending booking (simulate payment completion).

        Only PENDING bookings can be confirmed.
        Checks booking hasn't expired (15-minute window).
        Sets status to CONFIRMED and clears expiration time.

        Args:
            request: HTTP request object.
            pk: Booking primary key.

        Returns:
            Response: Confirmation message with updated booking.
        """
        booking = self.get_object()
        serializer = self.get_serializer(booking, data={})
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()

        output_serializer = BookingDetailSerializer(updated_booking)
        return Response({
            'message': 'Booking confirmed successfully.',
            'booking': output_serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Disable DELETE method for bookings.

        Bookings should be cancelled via the cancel action, not deleted.
        This preserves booking history for analytics and auditing.

        Returns:
            Response: 405 Method Not Allowed.
        """
        return Response(
            {'detail': 'Use the cancel endpoint to cancel bookings.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )