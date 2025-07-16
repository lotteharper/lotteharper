def get_past_date(age):
    from dateutil.relativedelta import relativedelta
    from django.conf import settings
    import pytz
    from django.utils import timezone
    return timezone.now() - relativedelta(years=settings.MIN_AGE_VERIFIED if not age else age) #.astimezone(pytz.timezone(settings.TIMEZONE))

def identity_verified_old(user):
    return True
    from django.contrib import messages
    if not user.profile.identity_verified or not user.profile.id_back_scanned or not user.profile.id_front_scanned:
        from feed.middleware import get_current_request
        messages.warning(get_current_request(), 'You need to verify your identity before you may see this page.')
        return False
    return True

def pediatric_identity_verified(user):
    from django.utils import timezone
    import datetime
    from django.conf import settings
    v = user.verifications.filter(submitted__gte=timezone.now() - datetime.timedelta(hours=settings.SIG_VALID_HOURS), verified=True).order_by('-submitted').first()
    if not v: return False
    if not v.birthday <= get_past_date(13):
        return False
    if not (user.profile.identity_verified or (v and v.verified)):
        from django.contrib import messages
        from feed.middleware import get_current_request
        messages.warning(get_current_request(), 'You need to verify your identity before you may see this page.')
        return False
    return True

def youngadult_identity_verified(user):
    from django.utils import timezone
    import datetime
    from django.conf import settings
    v = user.verifications.filter(submitted__gte=timezone.now() - datetime.timedelta(hours=settings.SIG_VALID_HOURS), verified=True).order_by('-submitted').first()
    if not v: return False
    if not v.birthday <= get_past_date(16):
        return False
    if not (user.profile.identity_verified or (v and v.verified)):
        from django.contrib import messages
        from feed.middleware import get_current_request
        messages.warning(get_current_request(), 'You need to verify your identity before you may see this page.')
        return False
    return True

def minor_identity_verified(user):
    from django.utils import timezone
    import datetime
    from django.conf import settings
    v = user.verifications.filter(submitted__gte=timezone.now() - datetime.timedelta(hours=settings.SIG_VALID_HOURS), verified=True).order_by('-submitted').first()
    if not v: return False
    if not v.birthday <= get_past_date(18):
        return False
    if not (user.profile.identity_verified or (v and v.verified)):
        from django.contrib import messages
        from feed.middleware import get_current_request
        messages.warning(get_current_request(), 'You need to verify your identity before you may see this page.')
        return False
    return True

def adult_identity_verified(user):
    from django.utils import timezone
    import datetime
    from django.conf import settings
    v = user.verifications.filter(submitted__gte=timezone.now() - datetime.timedelta(hours=settings.SIG_VALID_HOURS), verified=True).order_by('-submitted').first()
    if not v: return False
    if not v.birthday <= get_past_date(21) or (not v.subjective):
        return False
    if not (user.profile.identity_verified or (v and v.verified)):
        from django.contrib import messages
        from feed.middleware import get_current_request
        messages.warning(get_current_request(), 'You need to verify your identity before you may see this page.')
        return False
    return True
