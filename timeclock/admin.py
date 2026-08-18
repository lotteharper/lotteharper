from django.contrib import admin
from .models import Shift


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "start_time", "end_time", "expired", "duration_display")
    list_filter = ("expired", "start_time")
    search_fields = ("user__username", "notes")

    def duration_display(self, obj):
        d = obj.duration(fallback_to_now=False)
        return str(d) if d is not None else "-"
    duration_display.short_description = "duration"
