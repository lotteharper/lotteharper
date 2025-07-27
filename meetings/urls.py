from django.urls import path
from . import views

app_name='meetings'

urlpatterns = [
    path('', views.meeting, name='new-meeting'),
    path('<uuid:meeting_id>/', views.meeting, name='meeting'),
]
