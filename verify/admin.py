from django.contrib import admin
from .models import IdentityDocument
from simple_history.admin import SimpleHistoryAdmin
# Register your models here.
admin.site.register(IdentityDocument, SimpleHistoryAdmin)
