# Python modules
from typing import Any

# Django modules

# Django Rest Framework modules
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import View

# Third-party modules

# Project modules
from apps.btick.models import (
    BookingStatus,
    EventStatus,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    VenueMembership,
    VenueRole,
)


# =============================================================================
# Module-Level Constants for Group Names
# =============================================================================

GROUP_CUSTOMERS: str = "Customers"
GROUP_ORGANIZERS: str = "Organizers"
GROUP_VENUE_MANAGERS: str = "Venue Managers"
GROUP_SUPPORT_STAFF: str = "Support Staff"
GROUP_ADMINS: str = "Admins"


# =============================================================================
# Group-Based Permission Classes
# =============================================================================


class IsInGroup(permissions.BasePermission):
    """
    Base class for group-based permissions.

    Subclasses should set the `group_name` attribute.
    """

    group_name: str | None = None

    def has_permission(self, request: Request, view: View) -> bool:
        """Check if user is authenticated and in the specified group."""
        if not request.user.is_authenticated:
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        return request.user.groups.filter(name=self.group_name).exists()


class IsCustomer(IsInGroup):
    """Permission for users in the 'Customers' group."""

    group_name: str = GROUP_CUSTOMERS
    message: str = "You must be a registered customer to perform this action."


class IsOrganizer(IsInGroup):
    """Permission for users in the 'Organizers' group."""

    group_name: str = GROUP_ORGANIZERS
    message: str = "You must be an organizer to perform this action."


class IsVenueManagerGroup(IsInGroup):
    """Permission for users in the 'Venue Managers' group."""

    group_name: str = GROUP_VENUE_MANAGERS
    message: str = "You must be a venue manager to perform this action."


class IsSupportStaff(IsInGroup):
    """Permission for users in the 'Support Staff' group."""

    group_name: str = GROUP_SUPPORT_STAFF
    message: str = "You must be support staff to perform this action."


class IsAdminGroup(IsInGroup):
    """Permission for users in the 'Admins' group."""

    group_name: str = GROUP_ADMINS
    message: str = "You must be an admin to perform this action."


class IsOrganizerOrAdmin(permissions.BasePermission):
    """Permission for users in either 'Organizers' or 'Admins' group."""

    message: str = "You must be an organizer or admin to perform this action."

    def has_permission(self, request: Request, view: View) -> bool:
        """Check if user is in Organizers or Admins group."""
        if not request.user.is_authenticated:
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        return request.user.groups.filter(
            name__in=[GROUP_ORGANIZERS, GROUP_ADMINS]
        ).exists()


class IsSupportOrAdmin(permissions.BasePermission):
    """Permission for users in either 'Support Staff' or 'Admins' group."""

    message: str = "You must be support staff or admin to perform this action."

    def has_permission(self, request: Request, view: View) -> bool:
        """Check if user is in Support Staff or Admins group."""
        if not request.user.is_authenticated:
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        return request.user.groups.filter(
            name__in=[GROUP_SUPPORT_STAFF, GROUP_ADMINS]
        ).exists()


# =============================================================================
# Object-Level Permission Classes
# =============================================================================


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.

    Assumes the model instance has a `user` attribute.
    """

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        """Allow read access to all, write access only to owner."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IsBookingOwner(permissions.BasePermission):
    """Permission to only allow booking owners to view/modify their bookings."""

    message: str = "You can only access your own bookings."

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        """Check if user owns the booking or is staff."""
        return obj.user == request.user or request.user.is_staff


class CanCancelOwnBooking(permissions.BasePermission):
    """Permission to cancel own pending bookings only."""

    message: str = "You can only cancel your own pending bookings."

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        """Check if user can cancel the booking."""
        if request.user.is_staff:
            return True
        return obj.user == request.user and obj.status == BookingStatus.PENDING


class IsOrganizationMember(permissions.BasePermission):
    """
    Permission to check if user is a member of the organization.

    Works with objects that have an `organization` attribute,
    or with Organization objects directly.
    """

    message: str = "You must be a member of this organization."

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        """Check if user is a member of the organization."""
        if request.user.is_staff or request.user.is_superuser:
            return True

        # If obj IS an Organization, check membership directly
        if isinstance(obj, Organization):
            organization = obj
        else:
            organization = getattr(obj, "organization", None)

        if not organization:
            return False

        return OrganizationMembership.objects.filter(
            user=request.user,
            organization=organization,
        ).exists()


class IsOrganizationOwnerOrManager(permissions.BasePermission):
    """
    Permission to check if user is an owner or manager of the organization.

    Required for creating/modifying events.
    Works with objects that have an `organization` attribute,
    or with Organization objects directly.
    """

    message: str = "You must be an owner or manager of this organization."

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        """Check if user is an owner or manager of the organization."""
        if request.user.is_staff or request.user.is_superuser:
            return True

        # If obj IS an Organization, check membership directly
        if isinstance(obj, Organization):
            organization = obj
        else:
            organization = getattr(obj, "organization", None)

        if not organization:
            return False

        return OrganizationMembership.objects.filter(
            user=request.user,
            organization=organization,
            role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER],
        ).exists()


class CanManageEvent(permissions.BasePermission):
    """
    Permission to manage events (create, update, delete).

    User must be organization owner/manager or staff.
    """

    message: str = "You don't have permission to manage this event."

    def has_permission(self, request: Request, view: View) -> bool:
        """Check if user can manage events."""
        if request.user.is_staff or request.user.is_superuser:
            return True
        # For create, check if user has any organization membership
        if request.method == "POST":
            return OrganizationMembership.objects.filter(
                user=request.user,
                role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER],
            ).exists()
        return True

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        """Check if user can manage specific event."""
        if request.user.is_staff or request.user.is_superuser:
            return True

        return OrganizationMembership.objects.filter(
            user=request.user,
            organization=obj.organization,
            role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER],
        ).exists()


class CanPublishEvent(permissions.BasePermission):
    """Permission to publish events (change status from DRAFT to PUBLISHED)."""

    message: str = "You don't have permission to publish this event."

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        """Check if user can publish the event."""
        if request.user.is_staff or request.user.is_superuser:
            return True

        return OrganizationMembership.objects.filter(
            user=request.user,
            organization=obj.organization,
            role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER],
        ).exists()


class CanViewEventBookings(permissions.BasePermission):
    """
    Permission to view bookings for an event.

    User must be organization member or staff.
    """

    message: str = "You don't have permission to view bookings for this event."

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        """Check if user can view event bookings."""
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Get the event from the booking
        event = obj.event_ticket.event if hasattr(obj, "event_ticket") else obj

        return OrganizationMembership.objects.filter(
            user=request.user,
            organization=event.organization,
        ).exists()


class IsVenueMember(permissions.BasePermission):
    """Permission to check if user is a member of the venue."""

    message: str = "You must be a member of this venue."

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        """Check if user is a member of the venue."""
        if request.user.is_staff or request.user.is_superuser:
            return True

        venue = getattr(obj, "venue", obj)

        return VenueMembership.objects.filter(
            user=request.user,
            venue=venue,
        ).exists()


class IsVenueManager(permissions.BasePermission):
    """Permission to check if user is a manager of the venue."""

    message: str = "You must be a manager of this venue."

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        """Check if user is a manager of the venue."""
        if request.user.is_staff or request.user.is_superuser:
            return True

        venue = getattr(obj, "venue", obj)

        return VenueMembership.objects.filter(
            user=request.user,
            venue=venue,
            role=VenueRole.MANAGER,
        ).exists()


class CanRefundBooking(permissions.BasePermission):
    """
    Permission to refund bookings.

    Only staff or organization managers can refund.
    """

    message: str = "You don't have permission to refund bookings."

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        """Check if user can refund the booking."""
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Organization managers can refund their event bookings
        return OrganizationMembership.objects.filter(
            user=request.user,
            organization=obj.event_ticket.event.organization,
            role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER],
        ).exists()


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission to allow read-only access to everyone.

    Only staff can modify.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Allow read access to all, write access only to staff."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff


class CanViewDraftEvents(permissions.BasePermission):
    """
    Permission to view draft (unpublished) events.

    Only organization members or staff can see drafts.
    """

    message: str = "You can only view published events."

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        """Check if user can view the event."""
        # Published events are visible to everyone
        if obj.status == EventStatus.PUBLISHED:
            return True

        if request.user.is_staff or request.user.is_superuser:
            return True

        # Draft/cancelled events only visible to org members
        return OrganizationMembership.objects.filter(
            user=request.user,
            organization=obj.organization,
        ).exists()
