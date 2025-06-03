from django.contrib import admin
from .models import DocumentScan
from simple_history.admin import SimpleHistoryAdmin

admin.site.register(DocumentScan, SimpleHistoryAdmin)
