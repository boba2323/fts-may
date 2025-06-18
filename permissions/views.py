from django.shortcuts import render
from django.http import HttpResponse
from django.views import generic
from django.conf import settings
from pprint import pprint
# your models
from .models import File, Folder, Modification, Tag, ActionLog

# Create your views here.
from rest_framework import permissions, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from fts_app.serializers import FileSerializer, FolderSerializer, UserSerializer, ActionLogSerializer, TagSerializer, ModificationSerializer
from .models import Team, TeamMembership, AccessCode
from .serializers import TeamSerializer, TeamMembershipSerializer, AccessCodeSerializer
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
# for downloads
from django.http import FileResponse
# custom throttling
from django.utils import timezone
from datetime import timedelta
# ----

# import custom permissions
from fts_app.permissions import IsAuthorOrReadOnly, TeamsAndRolesFiles, TeamsAndRolesFolders

User = get_user_model()

class TeamViewSet(viewsets.ModelViewSet):
    serializer_class= TeamSerializer
    queryset = Team.objects.all()
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]

    # def get_permissions(self):
    #     if self.action in ['create', 'update', 'partial_update', 'destroy']:
    #         return [IsAuthenticated()]
    #     return super().get_permissions()

class TeamMembershipViewSet(viewsets.ModelViewSet):
    queryset = TeamMembership.objects.all()  # Adjust this to your actual queryset
    serializer_class = TeamMembershipSerializer
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]

    # def get_permissions(self):
    #     if self.action in ['create', 'update', 'partial_update', 'destroy']:
    #         return [IsAuthenticated()]
    #     return super().get_permissions()

class AccessCodeViewSet(viewsets.ModelViewSet):
    queryset = AccessCode.objects.all()  # Adjust this to your actual queryset
    serializer_class = AccessCodeSerializer
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]

    # def get_permissions(self):
    #     if self.action in ['create', 'update', 'partial_update', 'destroy']:
    #         return [IsAuthenticated()]
    #     return super().get_permissions()