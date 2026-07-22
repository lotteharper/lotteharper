from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('<str:name>/', views.booking_calendar, name='booking_calendar'),
    path('api/available-times/', views.get_available_times, name='get_available_times'),
    path('api/create-booking/', views.create_booking, name='create_booking'),
]
