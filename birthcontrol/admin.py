from django.contrib import admin
from .models import BirthControlProfile, BirthControlPill
from simple_history.admin import SimpleHistoryAdmin
# Register your models here.

admin.site.register(BirthControlProfile, SimpleHistoryAdmin)
admin.site.register(BirthControlPill, SimpleHistoryAdmin)
