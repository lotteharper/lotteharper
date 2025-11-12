from django.urls import path
from . import views

app_name='meetings'

urlpatterns = [
    path('schedule/', views.schedule_meeting, name='schedule-meeting'),
    path('', views.meeting, name='new-meeting'),
    path('<uuid:meeting_id>/', views.meeting, name='meeting'),
]
