from django.contrib import admin
from .models import Profile
from simple_history.admin import SimpleHistoryAdmin
# Register your models here.
admin.site.register(Profile, SimpleHistoryAdmin)
from simple_history import register
from django.contrib.auth.models import User
register(User)
