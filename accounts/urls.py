from django.urls import path
from . import views
from django.views.generic import DetailView, ListView, TemplateView
from .models import Myuser
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

app_name = "accounts"
urlpatterns = [
    path("userindex/", TemplateView.as_view(template_name="accounts/index.html"), name="userindex"),
    path('signup/', views.RegisterView.as_view(), name='signup'),

    path('api/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', views.CustomRefreshTokenView.as_view(), name='token_refresh'), 
    path('me/', views.LoggedUserView.as_view(), name="me"),
]
