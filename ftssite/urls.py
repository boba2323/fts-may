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
# ==========import views from different apps==========
from fts_app import views as fts_app_views
from permissions import views as permissions_views
# ====================================================


from debug_toolbar.toolbar import debug_toolbar_urls
from rest_framework.urlpatterns import format_suffix_patterns
from django.conf import settings
from django.conf.urls.static import static


router = routers.DefaultRouter()
router.register(r'users', fts_app_views.UsersViewSet, basename='myuser')
router.register(r'files', fts_app_views.FileViewSet, basename='file')
router.register(r'tags', fts_app_views.TagsViewSet, basename='tag')
router.register(r'folders', fts_app_views.FolderViewSet, basename='folder')

router.register(r'modifications', fts_app_views.ModificationViewSet, basename='modification')
router.register(r'actionlog', fts_app_views.ActionLogViewSet, basename='actionlog')

router.register(r'teams', permissions_views.TeamViewSet, basename='team')
router.register(r'teammembership', permissions_views.TeamMembershipViewSet, basename='teammembership')
router.register(r'accesscode', permissions_views.AccessCodeViewSet, basename='accesscode')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('fts_app.urls')),
    path('accounts/', include('accounts.urls')),  # Include the URLs from the fts_app
    
    # drf views
    path('drf/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls'))
] + debug_toolbar_urls()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# urlpatterns = format_suffix_patterns(urlpatterns)
# curl \
#   -X POST \
#   -H "Content-Type: application/json" \
#   -d '{"email": "deadryefield@gmail.com", "password": "b"}' \
#   http://localhost:8000/api/token/
