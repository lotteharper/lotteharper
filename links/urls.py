from django.urls import path
from . import views

app_name='links'

urlpatterns = [
    path('@<str:username>', views.links, name='links'),
]
