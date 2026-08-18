from django.urls import path
from . import views

app_name = "timeclock"

urlpatterns = [
    path("", views.shift_list, name="shift_list"),
    path("punch-in/", views.punch_in, name="punch_in"),
    path("punch-out/", views.punch_out, name="punch_out"),
    path("monthly/", views.monthly_summary, name="monthly_summary"),
]
