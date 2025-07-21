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
