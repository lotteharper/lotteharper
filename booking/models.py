from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import time, timedelta, datetime
from django.contrib.auth.models import User

class Booking(models.Model):
    """Model for storing hourly bookings"""
    title = models.CharField(max_length=255)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='vendor_bookings', null=True, blank=True)
    client = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='client_bookings', null=True, blank=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['date', 'start_time']

    def __str__(self):
        return f"{self.title} - {self.date} {self.start_time}"

    def clean(self):
        """Validate that booking date is not in the past"""
        now = timezone.now()
        today = now.date()
        current_time = now.time()
        
        if self.date is None:
            raise ValidationError("Booking date is required.")
        
        if self.date < today:
            raise ValidationError(
                "Cannot create bookings for past dates. Please select a date from today onwards."
            )
        
        # If booking is for today, ensure time hasn't passed
        if self.date == today:
            if self.start_time and self.start_time <= current_time:
                raise ValidationError(
                    f"Cannot create bookings for past times. Current time is {current_time.strftime('%H:%M')}."
                )

    def save(self, *args, **kwargs):
        """Call full_clean to trigger validation before saving"""
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_available_slots(cls, date):
        """Get all available time slots for a given date"""
        now = timezone.now()
        today = now.date()
        current_time = now.time()
        
        # Don't allow bookings for past dates
        if date is None or date < today:
            return []
        
        booked_slots = cls.objects.filter(date=date, is_booked=True).values_list('start_time', flat=True)
        business_hours = {
            'start': time(9, 0),  # 9 AM
            'end': time(17, 0)    # 5 PM
        }
        
        available_slots = []
        current_datetime = datetime.combine(date, business_hours['start'])
        end_datetime = datetime.combine(date, business_hours['end'])
        
        while current_datetime < end_datetime:
            slot_time = current_datetime.time()
            
            # If booking is for today, skip times that have already passed or are current
            if date == today and slot_time <= current_time:
                current_datetime += timedelta(hours=1)
                continue
            
            # Check if slot is already booked
            if slot_time not in booked_slots:
                available_slots.append(slot_time.strftime('%H:%M'))
            
            current_datetime += timedelta(hours=1)
        
        return available_slots

    @classmethod
    def get_booked_times(cls, date):
        """Get all booked time slots for a given date"""
        if date is None:
            return []
        return list(cls.objects.filter(date=date, is_booked=True).values_list('start_time', flat=True))

