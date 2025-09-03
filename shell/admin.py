from django.contrib import admin
from .models import ShellLogin
from simple_history.admin import SimpleHistoryAdmin
admin.site.register(ShellLogin, SimpleHistoryAdmin)

