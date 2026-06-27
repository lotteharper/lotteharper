from django.urls import path
from . import views

app_name='app'

urlpatterns = [
    path('app/', views.app, name='/'),
    path('app/', views.app, name='app'),
]
