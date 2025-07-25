def has_scan_privledge(user):
    return user.idware_privledge.objects.last() and user.idware_privledge.objects.last().active

def get_past_date(age):
    from django.utils import timezone
    from dateutil.relativedelta import relativedelta
    from django.conf import settings
    import pytz
    return timezone.now() - relativedelta(years=settings.MIN_AGE_VERIFIED if not age else age) #.astimezone(pytz.timezone(settings.TIMEZONE))

def pediatric_identity_verified(user):
    from verify.models import IdentityDocument
    import datetime
    from django.utils import timezone
    from django.conf import settings
    scan = IdentityDocument.objects.filter(user=user, verified=True, submitted__gte=timezone.now() - datetime.timedelta(hours=settings.SIG_VALID_HOURS)).order_by('-submitted').first()
    if scan and scan.birthday <= get_past_date(13):
        return True
    return False

def youngadult_identity_verified(user):
    from verify.models import IdentityDocument
    import datetime
    from django.utils import timezone
    from django.conf import settings
    scan = IdentityDocument.objects.filter(user=user, verified=True, submitted__gte=timezone.now() - datetime.timedelta(hours=settings.SIG_VALID_HOURS)).order_by('-submitted').first()
    if scan and scan.birthday <= get_past_date(16):
        return True
    return False

def minor_identity_verified(user):
    from verify.models import IdentityDocument
    import datetime
    from django.utils import timezone
    from django.conf import settings
    scan = IdentityDocument.objects.filter(user=user, verified=True, submitted__gte=timezone.now() - datetime.timedelta(hours=settings.SIG_VALID_HOURS)).order_by('-submitted').first()
    if scan and scan.birthday <= get_past_date(18):
        return True
    return False

def adult_identity_verified(user):
    from verify.models import IdentityDocument
    import datetime
    from django.utils import timezone
    from django.conf import settings
    scan = IdentityDocument.objects.filter(user=user, verified=True, submitted__gte=timezone.now() - datetime.timedelta(hours=settings.SIG_VALID_HOURS)).order_by('-submitted').first()
    if scan and scan.birthday <= get_past_date(21) or not scan.subjective:
        return True
    return False

