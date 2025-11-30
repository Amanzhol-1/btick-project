"""
Management command to create permission groups for the BTick application.

Usage:
    python manage.py setup_groups

This command creates the following groups with predefined permissions:
    - Customers: Basic user permissions for browsing and booking
    - Organizers: Event and ticket management permissions
    - Venue Managers: Venue management permissions
    - Support Staff: Customer support and booking management
    - Admins: Full access to all features
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Create permission groups for BTick application'

    # Group definitions with their permissions
    GROUPS = {
        'Customers': {
            'btick': {
                'booking': ['add_booking', 'view_own_bookings', 'cancel_own_booking'],
                'event': ['view_event'],
                'eventsticket': ['view_eventsticket'],
                'venue': ['view_venue'],
                'organization': ['view_organization'],
                'eventcategory': ['view_eventcategory'],
            }
        },
        'Organizers': {
            'btick': {
                'organization': [
                    'view_organization',
                    'view_own_organization',
                    'manage_organization_events',
                    'view_organization_analytics',
                ],
                'event': [
                    'add_event',
                    'change_event',
                    'view_event',
                    'publish_event',
                    'cancel_event',
                    'view_draft_events',
                    'view_event_analytics',
                    'manage_event_tickets',
                ],
                'eventsticket': [
                    'add_eventsticket',
                    'change_eventsticket',
                    'view_eventsticket',
                    'view_ticket_inventory',
                    'adjust_ticket_quota',
                    'view_ticket_sales',
                ],
                'booking': [
                    'view_booking',
                    'view_event_bookings',
                    'confirm_booking',
                ],
                'venue': ['view_venue'],
                'eventcategory': ['view_eventcategory'],
            }
        },
        'Venue Managers': {
            'btick': {
                'venue': [
                    'view_venue',
                    'change_venue',
                    'view_venue_schedule',
                    'manage_venue_capacity',
                    'view_venue_analytics',
                ],
                'event': ['view_event'],
                'eventcategory': ['view_eventcategory'],
            }
        },
        'Support Staff': {
            'btick': {
                'booking': [
                    'view_booking',
                    'change_booking',
                    'view_event_bookings',
                    'confirm_booking',
                    'refund_booking',
                ],
                'event': [
                    'view_event',
                    'view_draft_events',
                    'view_event_analytics',
                ],
                'eventsticket': [
                    'view_eventsticket',
                    'view_ticket_inventory',
                    'view_ticket_sales',
                ],
                'organization': [
                    'view_organization',
                    'view_organization_analytics',
                ],
                'venue': [
                    'view_venue',
                    'view_venue_schedule',
                    'view_venue_analytics',
                ],
                'eventcategory': ['view_eventcategory'],
            }
        },
        'Admins': {
            'btick': {
                'organization': [
                    'add_organization',
                    'change_organization',
                    'delete_organization',
                    'view_organization',
                    'view_own_organization',
                    'manage_organization_events',
                    'view_organization_analytics',
                    'manage_organization_members',
                ],
                'venue': [
                    'add_venue',
                    'change_venue',
                    'delete_venue',
                    'view_venue',
                    'view_venue_schedule',
                    'manage_venue_capacity',
                    'view_venue_analytics',
                ],
                'eventcategory': [
                    'add_eventcategory',
                    'change_eventcategory',
                    'delete_eventcategory',
                    'view_eventcategory',
                ],
                'event': [
                    'add_event',
                    'change_event',
                    'delete_event',
                    'view_event',
                    'publish_event',
                    'cancel_event',
                    'view_draft_events',
                    'view_event_analytics',
                    'manage_event_tickets',
                ],
                'eventsticket': [
                    'add_eventsticket',
                    'change_eventsticket',
                    'delete_eventsticket',
                    'view_eventsticket',
                    'view_ticket_inventory',
                    'adjust_ticket_quota',
                    'view_ticket_sales',
                ],
                'booking': [
                    'add_booking',
                    'change_booking',
                    'delete_booking',
                    'view_booking',
                    'view_own_bookings',
                    'cancel_own_booking',
                    'view_event_bookings',
                    'confirm_booking',
                    'refund_booking',
                ],
                'organizationmembership': [
                    'add_organizationmembership',
                    'change_organizationmembership',
                    'delete_organizationmembership',
                    'view_organizationmembership',
                ],
                'venuemembership': [
                    'add_venuemembership',
                    'change_venuemembership',
                    'delete_venuemembership',
                    'view_venuemembership',
                ],
            },
            'accounts': {
                'user': [
                    'add_user',
                    'change_user',
                    'delete_user',
                    'view_user',
                ],
            },
        },
    }

    def handle(self, *args, **options):
        self.stdout.write('Creating permission groups...\n')

        for group_name, apps in self.GROUPS.items():
            group, created = Group.objects.get_or_create(name=group_name)
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'\n{action} group: {group_name}')

            # Clear existing permissions to update them
            group.permissions.clear()

            for app_label, models in apps.items():
                for model_name, permission_codenames in models.items():
                    for codename in permission_codenames:
                        try:
                            permission = Permission.objects.get(
                                codename=codename,
                                content_type__app_label=app_label,
                                content_type__model=model_name,
                            )
                            group.permissions.add(permission)
                            self.stdout.write(
                                self.style.SUCCESS(f'  + {app_label}.{codename}')
                            )
                        except Permission.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  ! Permission not found: {app_label}.{model_name}.{codename}'
                                )
                            )

        self.stdout.write(self.style.SUCCESS('\nPermission groups setup complete!'))

        # Print summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('SUMMARY')
        self.stdout.write('=' * 50)
        for group_name in self.GROUPS.keys():
            group = Group.objects.get(name=group_name)
            perm_count = group.permissions.count()
            self.stdout.write(f'{group_name}: {perm_count} permissions')
