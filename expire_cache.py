import os, sys
if len(sys.argv) < 2:
    print('No path supplied')
    sys.exit(0)
print('Expiring cache for path {}'.format(sys.argv[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

def expire_page_cache(path):
    """
    Expires the cache for a specific page path.
    """
    from django.core.cache import cache
    from django.http import HttpRequest
    from django.utils.cache import get_cache_key
    request = HttpRequest()
    request.path = path
    request.META['SERVER_NAME'] = 'lotteh.com'
    request.META['SERVER_PORT'] = '443'
    # If your cached view uses Vary headers (e.g., Vary: Cookie), 
    # you might need to simulate the relevant request headers for get_cache_key 
    # to generate the correct key.
    key = get_cache_key(request)
    if key and cache.has_key(key):
        cache.delete(key)
        print(f"Cache cleared for path: {path}")
    else:
        print(f"No cache found for path: {path}")

expire_page_cache(sys.argv[1])
