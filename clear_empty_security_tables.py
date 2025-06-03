import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

from security.models import *

Credential.objects.all().delete()
UserLogin.objects.all().delete()
UserSession.objects.all().delete()
OTPToken.objects.all().delete()
Biometric.objects.all().delete()
Pincode.objects.all().delete()
MRZScan.objects.all().delete()
NFCScan.objects.all().delete()
VivoKeyScan.objects.all().delete()
UserIpAddress.objects.all().delete()
SecurityProfile.objects.all().delete()
Session.objects.all().delete()
SessionDedup.objects.all().delete()
