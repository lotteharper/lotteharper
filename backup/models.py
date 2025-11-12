from django.db import models
from django.utils import timezone

from lotteh.storages import BackupMediaStorage

def get_file_path(instance, filename):
    import uuid
    import os
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (str(uuid.uuid4()), ext)
    return os.path.join('backup/', filename)


class PublicBackup(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(default=timezone.now)
    file = models.FileField(storage=BackupMediaStorage, upload_to=get_file_path, null=True, blank=True)
