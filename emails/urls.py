from django.urls import path
from . import views

urlpatterns = [
    path("send/", views.send_email_page, name="send_email_page"),
]