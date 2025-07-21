def get_past_date(age):
    from django.utils import timezone
    from dateutil.relativedelta import relativedelta
    from django.conf import settings
    import pytz
    return timezone.now() - relativedelta(years=settings.MIN_AGE_VERIFIED if not age else age) #.astimezone(pytz.timezone(settings.TIMEZONE))

def pediatric_document_scanned(user):
    from barcode.models import DocumentScan
    import datetime
    from django.utils import timezone
    from django.conf import settings
    scan = DocumentScan.objects.filter(user=user, verified=True, side=True, foreign=False, timestamp__gte=timezone.now() - datetime.timedelta(hours=settings.ID_VALID_HOURS)).order_by('-timestamp').first()
    if scan.birthday <= get_past_date(13):
        return True
    return False

def youngadult_document_scanned(user):
    from barcode.models import DocumentScan
    import datetime
    from django.utils import timezone
    from django.conf import settings
    scan = DocumentScan.objects.filter(user=user, verified=True, side=True, foreign=False, timestamp__gte=timezone.now() - datetime.timedelta(hours=settings.ID_VALID_HOURS)).order_by('-timestamp').first()
    if scan.birthday <= get_past_date(16):
        return True
    return False

def minor_document_scanned(user):
    from barcode.models import DocumentScan
    import datetime
    from django.utils import timezone
    from django.conf import settings
    scan = DocumentScan.objects.filter(user=user, verified=True, side=True, foreign=False, timestamp__gte=timezone.now() - datetime.timedelta(hours=settings.ID_VALID_HOURS)).order_by('-timestamp').first()
    if scan.birthday <= get_past_date(18):
        return True
    return False

def adult_document_scanned(user):
    from barcode.models import DocumentScan
    import datetime
    from django.utils import timezone
    from django.conf import settings
    scan = DocumentScan.objects.filter(user=user, verified=True, side=True, foreign=False, timestamp__gte=timezone.now() - datetime.timedelta(hours=settings.ID_VALID_HOURS)).order_by('-timestamp').first()
    if scan.birthday <= get_past_date(21) or not scan.subjective:
        return True
    return False

