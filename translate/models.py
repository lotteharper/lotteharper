from django.db import models
from django.conf import settings
from django.utils import timezone

class CachedTranslation(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(default=timezone.now)
    src = models.CharField(default=settings.DEFAULT_LANG, max_length=10)
    dest = models.CharField(default=settings.DEFAULT_LANG, max_length=10)
    src_hash = models.CharField(max_length=100, default='', null=True, blank=True)
    src_content = models.TextField(default='')
    dest_content = models.TextField(default='')
    pronunciation = models.TextField(default='', blank=True, null=True)

    def populate_hash(self):
        self.src_hash = f"{self.src}:{self.dest}:{hash(self.src_content)}"
        self.save()
