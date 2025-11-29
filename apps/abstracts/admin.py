from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin

from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.admin import ModelAdmin


class SoftDeleteFilter(admin.SimpleListFilter):
    """
    Custom filter to easily toggle between active and deleted items.
    """
    title = 'status'
    parameter_name = 'soft_delete_status'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Active only'),
            ('deleted', 'Deleted only'),
            ('all', 'All'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(deleted_at__isnull=True)
        elif self.value() == 'deleted':
            return queryset.filter(deleted_at__isnull=False)
        return queryset

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup or (self.value() is None and lookup == 'active'),
                'query_string': changelist.get_query_string({self.parameter_name: lookup}),
                'display': title,
            }


class SoftDeleteAdmin:
    """
    Admin mixin to ensure soft delete is used instead of hard delete.
    Overrides both the queryset delete (bulk actions) and individual delete.
    Also shows soft-deleted items in the admin list view.
    """

    def get_queryset(self, request):
        """Return all objects including soft-deleted ones"""
        qs = self.model.objects.all()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def delete_queryset(self, request, queryset):
        """Override bulk delete to use soft delete"""
        queryset.delete()

    def delete_model(self, request, obj):
        """Override individual delete to use soft delete"""
        obj.delete()


admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
