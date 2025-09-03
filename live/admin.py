from django.contrib import admin
from .models import VideoRecording, VideoFrame, VideoCamera
from simple_history.admin import SimpleHistoryAdmin
# Register your models here.

admin.site.register(VideoRecording, SimpleHistoryAdmin)
admin.site.register(VideoFrame)
admin.site.register(VideoCamera)

