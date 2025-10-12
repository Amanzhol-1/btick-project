from django.db import models
from django.utils import timezone


class CreatedAtMixin(models.Model):
    """
    Adds a created_at field to the model

    Fields:
        created_at: TimeStamp automatically set on insert
    """
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class UpdatedAtMixin(models.Model):
    """
    Adds updated_at field to the model

    Fields:
        updated_at: TimeStamp automatically set on each save()
    """
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet aware of soft deleted row"""
    def alive(self) -> "SoftDeleteQuerySet":
        return self.filter(deleted_at__isnull=True)

    def dead(self) -> "SoftDeleteQuerySet":
        return self.exclude(deleted_at__isnull=True)


class SoftDeleteManager(models.Manager):
    """Manager for hide soft deleted rows"""
    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class AllObjectManager(SoftDeleteManager):
    """Manager exposing all rows including soft deleted rows"""
    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteMixin(models.Model):
    """
    Enables soft deletion via 'deleted_at' timestamp
    """
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectManager()

    class Meta:
        abstract = True

    def delete(self, using: str | None = None, keep_parents: bool = False) -> None:
        """Soft delete by setting deleted_at when delete row"""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self, using: str | None = None, keep_parents: bool = False) -> None:
        """Hard delete by setting deleted_at when delete row"""
        super().delete(using=using, keep_parents=keep_parents)


class VersionedMixin(models.Model):
    """
    Adds optimistic locking support by 'version' field

    Contract:
        Increment 'version' from service layer when applying state-changing updated
    """
    version = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        abstract = True

    def bump_version(self):
        self.version = (self.version or 0) + 1


class BaseEntity(CreatedAtMixin, UpdatedAtMixin, SoftDeleteMixin, VersionedMixin, models.Model):
    """
    Abstract base entity model

    Includes:
        - created_at, updated_at
        - deleted_at ( soft delete ) with dedicated managers
        - version ( optimistic lock )
    """
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
