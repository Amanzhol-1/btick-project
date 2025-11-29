from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Organization,
    Venue,
    EventCategory,
    Event,
    EventsTicket,
    Booking
)
from unfold.admin import ModelAdmin
from apps.abstracts.admin import SoftDeleteAdmin, SoftDeleteFilter


@admin.register(Organization)
class OrganizationAdmin(SoftDeleteAdmin, ModelAdmin):
    list_display = (
        "name",
        "website",
        "contact_email",
        "is_active",
        "created_at",
        "deleted_at"
    )
    list_filter = (SoftDeleteFilter, "is_active", "created_at")
    search_fields = ("name", "contact_email", "website")
    readonly_fields = ("created_at", "updated_at", "deleted_at")
    ordering = ("name",)


@admin.register(Venue)
class VenueAdmin(SoftDeleteAdmin, ModelAdmin):
    list_display = (
        "name",
        "address",
        "capacity",
        "is_active",
        "created_at",
        "deleted_at"
    )
    list_filter = (SoftDeleteFilter, "is_active", "created_at")
    search_fields = ("name", "address")
    readonly_fields = ("created_at", "updated_at", "deleted_at")
    ordering = ("name",)


@admin.register(EventCategory)
class EventCategoryAdmin(SoftDeleteAdmin, ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "created_at",
        "deleted_at"
    )
    list_filter = (SoftDeleteFilter, "is_active")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at", "deleted_at")
    ordering = ("name",)


@admin.register(Event)
class EventAdmin(SoftDeleteAdmin, ModelAdmin):
    list_display = (
        "title",
        "organization",
        "venue",
        "category",
        "starts_at",
        "ends_at",
        "status",
        "capacity",
        "deleted_at"
    )
    list_filter = (SoftDeleteFilter, "status", "category", "organization", "starts_at", "is_active")
    search_fields = ("title", "description", "organization__name", "venue__name")
    list_select_related = ("organization", "venue", "category")
    readonly_fields = ("created_at", "updated_at", "deleted_at")
    ordering = ("-starts_at",)
    date_hierarchy = "starts_at"

    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "description", "status")
        }),
        ("Relations", {
            "fields": ("organization", "venue", "category")
        }),
        ("Schedule & Capacity", {
            "fields": ("starts_at", "ends_at", "capacity")
        }),
        ("System Fields", {
            "fields": ("is_active", "created_at", "updated_at", "deleted_at"),
            "classes": ("collapse",)
        })
    )


@admin.register(EventsTicket)
class EventsTicketAdmin(SoftDeleteAdmin, ModelAdmin):
    list_display = (
        "ticket_type",
        "event",
        "price",
        "quota",
        "sold",
        "available_tickets",
        "is_active",
        "deleted_at"
    )
    list_filter = (SoftDeleteFilter, "ticket_type", "is_active", "created_at")
    search_fields = ("event__title",)
    list_select_related = ("event",)
    readonly_fields = ("sold", "created_at", "updated_at", "deleted_at", "available_tickets")
    ordering = ("event", "ticket_type")

    fieldsets = (
        ("Ticket Information", {
            "fields": ("event", "ticket_type", "price")
        }),
        ("Availability", {
            "fields": ("quota", "sold", "available_tickets")
        }),
        ("System Fields", {
            "fields": ("is_active", "created_at", "updated_at", "deleted_at"),
            "classes": ("collapse",)
        })
    )

    @admin.display(description="Available")
    def available_tickets(self, obj):
        remaining = obj.quota - obj.sold
        if remaining <= 0:
            color = "red"
        elif remaining < obj.quota * 0.2:
            color = "orange"
        else:
            color = "green"
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            remaining
        )


@admin.register(Booking)
class BookingAdmin(SoftDeleteAdmin, ModelAdmin):
    list_display = (
        "id",
        "user",
        "event_ticket",
        "quantity",
        "status",
        "expires_at",
        "created_at",
        "deleted_at"
    )
    list_filter = (SoftDeleteFilter, "status", "created_at", "expires_at")
    search_fields = (
        "user__email",
        "user__username",
        "event_ticket__event__title",
        "event_ticket__ticket_type"
    )
    list_select_related = ("user", "event_ticket", "event_ticket__event")
    readonly_fields = ("created_at", "updated_at", "deleted_at")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    fieldsets = (
        ("Booking Details", {
            "fields": ("user", "event_ticket", "quantity", "status")
        }),
        ("Timing", {
            "fields": ("expires_at",)
        }),
        ("System Fields", {
            "fields": ("is_active", "created_at", "updated_at", "deleted_at"),
            "classes": ("collapse",)
        })
    )