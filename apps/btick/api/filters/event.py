import django_filters

from apps.btick.models import Event


class EventFilter(django_filters.FilterSet):
    """
    Filter class for Event queryset.

    Provides filtering capabilities for event listing endpoint.
    Supports filtering by category, venue, organization, status, and date ranges.
    """

    category = django_filters.NumberFilter(field_name='category__id')
    venue = django_filters.NumberFilter(field_name='venue__id')
    organization = django_filters.NumberFilter(field_name='organization__id')

    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=[('DRAFT', 'Draft'), ('PUBLISHED', 'Published'), ('CANCELLED', 'Cancelled')]
    )

    starts_after = django_filters.IsoDateTimeFilter(
        field_name='starts_at',
        lookup_expr='gte',
        help_text='Filter events starting after this datetime (ISO format)'
    )
    starts_before = django_filters.IsoDateTimeFilter(
        field_name='starts_at',
        lookup_expr='lte',
        help_text='Filter events starting before this datetime (ISO format)'
    )
    ends_after = django_filters.IsoDateTimeFilter(
        field_name='ends_at',
        lookup_expr='gte',
        help_text='Filter events ending after this datetime (ISO format)'
    )
    ends_before = django_filters.IsoDateTimeFilter(
        field_name='ends_at',
        lookup_expr='lte',
        help_text='Filter events ending before this datetime (ISO format)'
    )

    class Meta:
        model = Event
        fields = [
            'category',
            'venue',
            'organization',
            'status',
            'starts_after',
            'starts_before',
            'ends_after',
            'ends_before',
        ]