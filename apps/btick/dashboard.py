import json

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

from apps.btick.models import Booking, BookingStatus


def get_booking_stats():
    """Get booking counts by status"""
    stats = Booking.objects.values('status').annotate(count=Count('id'))
    return {item['status']: item['count'] for item in stats}


def get_booking_chart_data():
    """Get data for bar chart"""
    stats = get_booking_stats()
    return {
        'labels': ['Pending', 'Confirmed', 'Cancelled'],
        'datasets': [{
            'data': [
                stats.get(BookingStatus.PENDING, 0),
                stats.get(BookingStatus.CONFIRMED, 0),
                stats.get(BookingStatus.CANCELLED, 0),
            ],
            'backgroundColor': ['#f59e0b', '#10b981', '#ef4444'],
        }]
    }


def get_recent_bookings():
    """Get 10 most recent bookings"""
    bookings = Booking.objects.select_related(
        'user', 'event_ticket__event'
    ).order_by('-created_at')[:10]

    return {
        'headers': ['User', 'Event', 'Ticket', 'Qty', 'Status', 'Created'],
        'rows': [
            [
                b.user.email,
                b.event_ticket.event.title[:20],
                b.event_ticket.ticket_type,
                b.quantity,
                b.status,
                b.created_at.strftime('%Y-%m-%d %H:%M'),
            ]
            for b in bookings
        ]
    }


def get_booking_trends():
    """Get booking counts for last 7 days"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=6)

    bookings_by_day = (
        Booking.objects
        .filter(created_at__date__gte=start_date)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    day_counts = {item['date']: item['count'] for item in bookings_by_day}
    labels = []
    data = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        labels.append(day.strftime('%a'))
        data.append(day_counts.get(day, 0))

    return {
        'labels': labels,
        'datasets': [{
            'label': 'Bookings',
            'data': data,
            'borderColor': '#6366f1',
            'tension': 0.1,
        }]
    }


def dashboard_callback(request, context):
    """Main dashboard callback for Unfold admin"""
    stats = get_booking_stats()

    context.update({
        'booking_stats': {
            'pending': stats.get(BookingStatus.PENDING, 0),
            'confirmed': stats.get(BookingStatus.CONFIRMED, 0),
            'cancelled': stats.get(BookingStatus.CANCELLED, 0),
            'total': sum(stats.values()) if stats else 0,
        },
        'booking_chart': json.dumps(get_booking_chart_data()),
        'recent_bookings': get_recent_bookings(),
        'booking_trends': json.dumps(get_booking_trends()),
    })
    return context
