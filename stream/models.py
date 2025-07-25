from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class ChatMessage(models.Model):
    id = models.AutoField(primary_key=True)
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stream_messages', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_stream_messages', null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    message = models.TextField(default='', null=True, blank=True)
