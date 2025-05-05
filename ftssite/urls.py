"""
URL configuration for ftssite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import routers
from fts_app import views
from debug_toolbar.toolbar import debug_toolbar_urls
from rest_framework.urlpatterns import format_suffix_patterns


router = routers.DefaultRouter()
router.register(r'users', views.UsersViewSet, basename='myuser')
router.register(r'files', views.FileViewSet, basename='files')
router.register(r'tags', views.TagsViewSet, basename='tags')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('fts_app.urls')),
    path('accounts/', include('accounts.urls')),  # Include the URLs from the fts_app

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    
    # drf views
    path('drf/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
] + debug_toolbar_urls()


# urlpatterns = format_suffix_patterns(urlpatterns)
# curl \
#   -X POST \
#   -H "Content-Type: application/json" \
#   -d '{"email": "deadryefield@gmail.com", "password": "b"}' \
#   http://localhost:8000/api/token/
