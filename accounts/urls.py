from django.urls import path
from . import views
from django.views.generic import DetailView, ListView, TemplateView
from .models import Myuser

app_name = "accounts"
urlpatterns = [
    path("userindex", TemplateView.as_view(template_name="accounts/index.html"), name="userindex"),
]