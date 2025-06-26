from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class SharedLink(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, related_name='shared_link', on_delete=models.CASCADE, null=True, blank=True)
    url = models.CharField(default='', null=True, blank=True)
    description = models.CharField(default='', null=True, blank=True)
    color = models.CharField(default='#FFFFFF', null=True, blank=True)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)
