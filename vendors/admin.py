from django.contrib import admin
from .models import VendorProfile
from simple_history.admin import SimpleHistoryAdmin
# Register your models here.
admin.site.register(VendorProfile, SimpleHistoryAdmin)
