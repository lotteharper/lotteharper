from django.urls import path
from . import views

app_name='stream'

urlpatterns = [
    path('', views.stream, name='stream'),
    path('<str:username>/', views.watch, name='watch'),
]
