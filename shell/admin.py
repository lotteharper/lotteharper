from django.contrib import admin
from .models import ShellLogin
admin.site.register(ShellLogin)
admin.site.register(ShellLogin.history.model)
