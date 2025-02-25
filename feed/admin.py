from django.contrib import admin
from .models import Post, Report, Bid
from django.contrib.admin.models import LogEntry
from simple_history.admin import SimpleHistoryAdmin

# Register your models here.
admin.site.register(Post, SimpleHistoryAdmin)
admin.site.register(Bid)
admin.site.register(Report)
admin.site.register(LogEntry)
