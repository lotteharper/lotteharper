from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('api/available-times/', views.get_available_times, name='get_available_times'),
    path('api/create-booking/', views.create_booking, name='create_booking'),
    path('times/<str:name>/', views.booked_times_list, name='booked_times_list'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('stats/', views.booking_stats, name='booking_stats'),
    path('<str:name>/', views.booking_calendar, name='booking_calendar'),
]
