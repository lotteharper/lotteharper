from django.db import models
import uuid

class Meeting(models.Model):
    id = models.AutoField(primary_key=True)
    identifier = models.UUIDField(default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
