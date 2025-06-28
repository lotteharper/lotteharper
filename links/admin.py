from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import SharedLink

admin.site.register(SharedLink, SimpleHistoryAdmin)
