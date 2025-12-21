# Python modules
from typing import Any, Generator

# Django modules
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from django.db.models import QuerySet
from django.http import HttpRequest

# Django Rest Framework modules

# Third-party modules
from unfold.admin import ModelAdmin

# Project modules


class SoftDeleteFilter(admin.SimpleListFilter):
    """Custom filter to easily toggle between active and deleted items."""

    title: str = "status"
    parameter_name: str = "soft_delete_status"

    def lookups(
        self,
        request: HttpRequest,
        model_admin: Any,
    ) -> tuple[tuple[str, str], ...]:
        """Return filter lookup options."""
        return (
            ("active", "Active only"),
            ("deleted", "Deleted only"),
            ("all", "All"),
        )

    def queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet[Any],
    ) -> QuerySet[Any] | None:
        """Filter queryset based on selected option."""
        if self.value() == "active":
            return queryset.filter(deleted_at__isnull=True)
        elif self.value() == "deleted":
            return queryset.filter(deleted_at__isnull=False)
        return queryset

    def choices(
        self,
        changelist: Any,
    ) -> Generator[dict[str, Any], None, None]:
        """Generate filter choices with default selection."""
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup or (self.value() is None and lookup == "active"),
                "query_string": changelist.get_query_string({self.parameter_name: lookup}),
                "display": title,
            }


class SoftDeleteAdmin:
    """
    Admin mixin to ensure soft delete is used instead of hard delete.

    Overrides both the queryset delete (bulk actions) and individual delete.
    Also shows soft-deleted items in the admin list view.
    """

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        """Return all objects including soft-deleted ones."""
        qs: QuerySet[Any] = self.model.objects.all()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[Any]) -> None:
        """Override bulk delete to use soft delete."""
        queryset.delete()

    def delete_model(self, request: HttpRequest, obj: Any) -> None:
        """Override individual delete to use soft delete."""
        obj.delete()


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    """Admin configuration for Django's Group model with Unfold styling."""

    pass
