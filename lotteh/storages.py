from storages.backends.s3boto3 import S3Boto3Storage
from django.core.files.storage import Storage
from django.core.cache import cache
from django.conf import settings
import os

class BackupMediaStorage(S3Boto3Storage):
    bucket_name = 'charlotteharper-backups'

    def _get_cache_key(self, name):
        return f'media_url_{name}'

    def url(self, name):
        cache_key = self._get_cache_key(name)
        cached_url = cache.get(cache_key)
        if cached_url:
            return cached_url

        url = super(MediaStorage, self).url(name)
        cache.set(cache_key, url, settings.MEDIA_URL_CACHE_TIMEOUT) # Set a timeout
        return url

    def delete(self, name):
        cache_key = self._get_cache_key(name)
        cache.delete(cache_key)
        super().delete(name)
