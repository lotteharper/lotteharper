from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def save_profile(sender, instance, created, **kwargs):
    if created:
        if not hasattr(instance, 'profile'):
            from .models import Profile
            Profile.objects.create(user=instance)
    if not hasattr(instance, 'security_profile'):
        from security.models import SecurityProfile
        SecurityProfile.objects.create(user=instance)

from django.contrib.auth.signals import user_logged_in

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    from users.models import AccountLink
    from security.models import UserSession, SecurityProfile
    from django.contrib.auth import login as auth_login
    from django.contrib.auth import authenticate, logout
    link = AccountLink.objects.filter(from_user=user).first()
    if link:
        logout(request)
        auth_login(request, link.to_user, backend='django.contrib.auth.backends.ModelBackend')
        user = link.to_user
    from security.apis import get_client_ip
    ip_address = get_client_ip(request)
    if not ip_address:
        from ipware import get_client_ip
        ip_address, is_routable = get_client_ip(request)
    from security.geolocation import get_ip_location, get_country
    latitude, longitude = get_ip_location(ip_address)
    country = None
    if latitude != None and longitude != None:
        country = get_country(latitude, longitude)
    UserSession.objects.get_or_create(user=user, ip_address=ip_address[:39] if ip_address else None, session_key=request.session.session_key, user_agent=request.META["HTTP_USER_AGENT"], authorized=False, latitude=latitude, longitude=longitude, country=country)
    if request.user.is_authenticated and not hasattr(request.user, 'security_profile') and isinstance(request.user, User):
        security_profile = SecurityProfile()
        security_profile.user = request.user
        security_profile.save()
