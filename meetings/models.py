from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import uuid

class Meeting(models.Model):
    id = models.AutoField(primary_key=True)
    identifier = models.UUIDField(default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class ChatMessage(models.Model):
    id = models.AutoField(primary_key=True)
    meeting_id = models.CharField(max_length=50, default='', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_meeting_messages', null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    message = models.TextField(default='', null=True, blank=True)
