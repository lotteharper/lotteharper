from django.urls import path
from . import views

app_name='links'

urlpatterns = [
    path('my/links/', views.my_links, name='my-links'),
    path('@<str:username>', views.links, name='links'),
    path('@<str:username>/', views.links, name='links-dash'),
]
