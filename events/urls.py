from django.urls import path
from . import views

app_name='events'

urlpatterns = [
    path('<str:event_id>/add-to-calendar/', views.add_to_calendar, name='add-to-calendar'),
]
