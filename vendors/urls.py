from django.urls import path

from . import views

app_name='vendors'

urlpatterns = [
    path('onboarding/', views.onboarding, name='onboarding'),
    path('preferences/', views.vendor_preferences, name='preferences'),
    path('crypto/', views.send_bitcoin, name='send-bitcoin'),
    path('adult/video/<str:username>/', views.video, name='video'),
    path('adult/content/<str:username>/', views.content, name='content'),
]
