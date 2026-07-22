from django.db import models
from datetime import time, timedelta, datetime
from simple_history.models import HistoricalRecords

class Booking(models.Model):
    """Model for storing hourly bookings"""
    title = models.CharField(max_length=255)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['date', 'start_time']

    def __str__(self):
        return f"{self.title} - {self.date} {self.start_time}"

    @classmethod
    def get_available_slots(cls, date):
        """Get all available time slots for a given date"""
        booked_slots = cls.objects.filter(date=date, is_booked=True).values_list('start_time', flat=True)
        business_hours = {'start': time(9, 0), 'end': time(17, 0)}
        
        available_slots = []
        current_time = datetime.combine(date, business_hours['start'])
        end_time = datetime.combine(date, business_hours['end'])
        
        while current_time < end_time:
            slot_time = current_time.time()
            if slot_time not in booked_slots:
                available_slots.append(slot_time.strftime('%H:%M'))
            current_time += timedelta(hours=1)
        
        return available_slots

    @classmethod
    def get_booked_times(cls, date):
        """Get all booked time slots for a given date"""
        return list(cls.objects.filter(date=date, is_booked=True).values_list('start_time', flat=True))
