from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        if not hasattr(sender, 'profile'):
            from .models import Profile
            Profile.objects.create(user=sender)
        if not hasattr(sender, 'security_profile'):
            from security.models import SecurityProfile
            SecurityProfile.objects.create(user=sender)
