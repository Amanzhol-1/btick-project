from rest_framework import permissions

from .models import OrganizationMembership, VenueMembership, OrganizationRole, VenueRole


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has a `user` attribute.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IsBookingOwner(permissions.BasePermission):
    """
    Permission to only allow booking owners to view/modify their bookings.
    """
    message = "You can only access your own bookings."

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff


class CanCancelOwnBooking(permissions.BasePermission):
    """
    Permission to cancel own pending bookings only.
    """
    message = "You can only cancel your own pending bookings."

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user and obj.status == 'PENDING'


class IsOrganizationMember(permissions.BasePermission):
    """
    Permission to check if user is a member of the organization.
    Works with objects that have an `organization` attribute.
    """
    message = "You must be a member of this organization."

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True

        organization = getattr(obj, 'organization', None)
        if not organization:
            return False

        return OrganizationMembership.objects.filter(
            user=request.user,
            organization=organization
        ).exists()


class IsOrganizationOwnerOrManager(permissions.BasePermission):
    """
    Permission to check if user is an owner or manager of the organization.
    Required for creating/modifying events.
    """
    message = "You must be an owner or manager of this organization."

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True

        organization = getattr(obj, 'organization', None)
        if not organization:
            return False

        return OrganizationMembership.objects.filter(
            user=request.user,
            organization=organization,
            role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER]
        ).exists()


class CanManageEvent(permissions.BasePermission):
    """
    Permission to manage events (create, update, delete).
    User must be organization owner/manager or staff.
    """
    message = "You don't have permission to manage this event."

    def has_permission(self, request, view):
        if request.user.is_staff or request.user.is_superuser:
            return True
        # For create, check if user has any organization membership
        if request.method == 'POST':
            return OrganizationMembership.objects.filter(
                user=request.user,
                role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER]
            ).exists()
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True

        return OrganizationMembership.objects.filter(
            user=request.user,
            organization=obj.organization,
            role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER]
        ).exists()


class CanPublishEvent(permissions.BasePermission):
    """
    Permission to publish events (change status from DRAFT to PUBLISHED).
    """
    message = "You don't have permission to publish this event."

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True

        return OrganizationMembership.objects.filter(
            user=request.user,
            organization=obj.organization,
            role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER]
        ).exists()


class CanViewEventBookings(permissions.BasePermission):
    """
    Permission to view bookings for an event.
    User must be organization member or staff.
    """
    message = "You don't have permission to view bookings for this event."

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Get the event from the booking
        event = obj.event_ticket.event if hasattr(obj, 'event_ticket') else obj

        return OrganizationMembership.objects.filter(
            user=request.user,
            organization=event.organization
        ).exists()


class IsVenueMember(permissions.BasePermission):
    """
    Permission to check if user is a member of the venue.
    """
    message = "You must be a member of this venue."

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True

        venue = getattr(obj, 'venue', obj)

        return VenueMembership.objects.filter(
            user=request.user,
            venue=venue
        ).exists()


class IsVenueManager(permissions.BasePermission):
    """
    Permission to check if user is a manager of the venue.
    """
    message = "You must be a manager of this venue."

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True

        venue = getattr(obj, 'venue', obj)

        return VenueMembership.objects.filter(
            user=request.user,
            venue=venue,
            role=VenueRole.MANAGER
        ).exists()


class CanRefundBooking(permissions.BasePermission):
    """
    Permission to refund bookings.
    Only staff or organization managers can refund.
    """
    message = "You don't have permission to refund bookings."

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Organization managers can refund their event bookings
        return OrganizationMembership.objects.filter(
            user=request.user,
            organization=obj.event_ticket.event.organization,
            role__in=[OrganizationRole.OWNER, OrganizationRole.MANAGER]
        ).exists()


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission to allow read-only access to everyone,
    but only staff can modify.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff


class CanViewDraftEvents(permissions.BasePermission):
    """
    Permission to view draft (unpublished) events.
    Only organization members or staff can see drafts.
    """
    message = "You can only view published events."

    def has_object_permission(self, request, view, obj):
        # Published events are visible to everyone
        if obj.status == 'PUBLISHED':
            return True

        if request.user.is_staff or request.user.is_superuser:
            return True

        # Draft/cancelled events only visible to org members
        return OrganizationMembership.objects.filter(
            user=request.user,
            organization=obj.organization
        ).exists()
