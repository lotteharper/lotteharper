from django.contrib import admin
from .models import Face
from simple_history.admin import SimpleHistoryAdmin

# Register your models here.
admin.site.register(Face, SimpleHistoryAdmin)
