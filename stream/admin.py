from django.contrib import admin
#from simple_history.admin import SimpleHistoryAdmin
from .models import ChatMessage

admin.site.register(ChatMessage)
