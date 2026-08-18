from simple_history.models import HistoricalRecords
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import F
from django.utils import timezone


class Shift(models.Model):
    """
    A Shift represents a single punch-in / punch-out window.
    - user: ForeignKey to AUTH_USER_MODEL so this works with custom user models.
    - start_time: when the user punched in
    - end_time: when they punched out (nullable until punched out)
    - expired: set when a shift was auto-expired (e.g. max length exceeded)
    - notes: optional text stored at punch-out
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shifts"
    )
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    expired = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ["-start_time"]

    def __str__(self):
        status = "active" if self.is_active else "closed"
        return f"Shift({self.user}, {self.start_time.isoformat()} -> {self.end_time.isoformat() if self.end_time else '...'}, {status})"

    @property
    def is_active(self):
        return self.end_time is None and not self.expired

    def duration(self, fallback_to_now=True):
        """
        Return a timedelta for this shift:
        - If end_time exists, end_time - start_time
        - Otherwise, timezone.now() - start_time if fallback_to_now True, else None
        """
        if self.end_time:
            return self.end_time - self.start_time
        if fallback_to_now:
            return timezone.now() - self.start_time
        return None

    def expire_if_older_than(self, hours=12):
        """
        Mark as expired and save if shift is active and older than `hours`.
        Returns True if changed, False otherwise.
        """
        if self.is_active and timezone.now() - self.start_time > timedelta(hours=hours):
            self.expired = True
            self.save(update_fields=["expired", "updated_at"])
            return True
        return False
