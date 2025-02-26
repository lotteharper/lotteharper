from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from simple_history.models import HistoricalRecords

class SavedFile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='file_edits', null=True)
    path = models.CharField(default='', null=True, blank=True, max_length=255)
    content = models.TextField(null=True, blank=True, default='')
    saved_at = models.DateTimeField(default=timezone.now)
    current = models.BooleanField(default=True)

class ShellLogin(models.Model):
    id = models.AutoField(primary_key=True)
    ip_address = models.CharField(max_length=39, default='', null=True, blank=True)
    time = models.DateTimeField(default=timezone.now)
    approved = models.BooleanField(default=False)
    validated = models.BooleanField(default=False)
    code = models.CharField(max_length=6, default='', null=True, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return '({}) - {} requested admin auth at {} with code {}, can auth? {}'.format(str(self.id), self.ip_address, self.time_format(), code, 'y' if self.approved and self.validated else 'n')

    def time_format(self):
        return self.time.strftime('%B %d, %Y, %H:%M:%S')
