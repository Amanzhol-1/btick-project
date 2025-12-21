# Python modules

# Django modules
from django.db import models
from django.utils import timezone

# Django Rest Framework modules

# Third-party modules

# Project modules


class CreatedAtMixin(models.Model):
    """
    Adds a created_at field to the model.

    Fields:
        created_at: TimeStamp automatically set on insert.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
        help_text="Timestamp when the record was created",
    )

    class Meta:
        """Meta options for CreatedAtMixin."""

        abstract = True


class UpdatedAtMixin(models.Model):
    """
    Adds updated_at field to the model.

    Fields:
        updated_at: TimeStamp automatically set on each save().
    """

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated at",
        help_text="Timestamp when the record was last updated",
    )

    class Meta:
        """Meta options for UpdatedAtMixin."""

        abstract = True


class IsActiveMixin(models.Model):
    """
    Adds is_active field to the model for enabling/disabling records.

    Fields:
        is_active: Boolean flag for active status.
    """

    is_active = models.BooleanField(
        default=True,
        verbose_name="Is active",
        help_text="Flag indicating whether the record is active",
    )

    class Meta:
        """Meta options for IsActiveMixin."""

        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    """
    QuerySet for models with soft delete support.

    Provides methods to filter active/deleted records.
    """

    def alive(self) -> "SoftDeleteQuerySet":
        """Return only non-deleted records."""
        return self.filter(deleted_at__isnull=True)

    def dead(self) -> "SoftDeleteQuerySet":
        """Return only soft-deleted records."""
        return self.filter(deleted_at__isnull=False)

    def delete(self) -> int:
        """Soft delete all objects in the queryset."""
        update: dict[str, object] = {"deleted_at": timezone.now()}
        if hasattr(self.model, "is_active"):
            update["is_active"] = False
        return self.update(**update)

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        """Permanently delete all objects in the queryset."""
        return super().delete()


class SoftDeleteMixin(models.Model):
    """
    Enables soft deletion via 'deleted_at' timestamp.

    Provides:
        - deleted_at field
        - Soft delete on instance.delete()
        - QuerySet methods: alive(), dead(), hard_delete()
        - Template method for extensions.
    """

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Deleted at",
        help_text="Timestamp when the record was soft deleted (null if active)",
    )

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        """Meta options for SoftDeleteMixin."""

        abstract = True

    def delete(self) -> None:
        """
        Soft delete by setting deleted_at timestamp.

        Calls _prepare_soft_delete() hook for extensions.
        """
        self.deleted_at = timezone.now()
        update_fields: list[str] = ["deleted_at"]

        additional_fields: list[str] = self._prepare_soft_delete()
        if additional_fields:
            update_fields.extend(additional_fields)

        self.save(update_fields=update_fields)

    def _prepare_soft_delete(self) -> list[str]:
        """
        Hook for subclasses to perform additional actions during soft delete.

        Returns:
            List of additional field names to include in update_fields.
        """
        return []

    def hard_delete(self) -> None:
        """Permanently delete the record from database."""
        super().delete()


class BaseEntity(CreatedAtMixin, UpdatedAtMixin, IsActiveMixin, SoftDeleteMixin, models.Model):
    """
    Abstract base entity model.

    Includes:
        - created_at, updated_at (timestamp tracking)
        - is_active (enable/disable flag)
        - deleted_at (soft delete)

    Behavior:
        - When soft deleted, is_active is automatically set to False
        - Use .alive() to filter only non-deleted records
        - Use .dead() to filter only deleted records.
    """

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        """Meta options for BaseEntity."""

        abstract = True

    def _prepare_soft_delete(self) -> list[str]:
        """
        Coordinate soft delete with is_active flag.

        When soft deleting, also mark the record as inactive.
        """
        self.is_active = False
        return ["is_active"]
