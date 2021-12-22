from django.urls import path

from . import views

app_name = "mailrelay"

urlpatterns = [
    path("", views.index, name="index"),
]
