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
from fts_app.serializers import FileSerializer, FolderSerializer, UserSerializer, GroupSerializer, ActionLogSerializer, TagSerializer, ModificationSerializer
from .models import File, Folder, Modification, Tag, ActionLog
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.decorators import action
# for downloads
from django.http import FileResponse
# custom throttling
from django.utils import timezone
from datetime import timedelta
# ----

# import custom permissions
from .permissions import IsAuthorOrReadOnly, TeamsAndRolesFiles,DownloadPermission, TeamsAndRolesFolders, RegisterUserPermission

# ==============from permissions app===================
from permissions.models import Team, TeamMembership, AccessCode




User = get_user_model()
class IndexView(generic.TemplateView):
    template_name = "fts_app/index.html"

# https://tech.serhatteker.com/post/2020-09/enable-partial-update-drf/
#  A viewset that provides default `create()`, `retrieve()`, `update()`,
#     `partial_update()`, `destroy()` and `list()` actions.
#     """

class Home(APIView):
    # authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        content = {'message': 'Hello, World!'}
        return Response(content)


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [RegisterUserPermission, IsAuthorOrReadOnly]
    authentication_classes = [JWTAuthentication]

    

class FileViewSet(viewsets.ModelViewSet):
    # queryset = File.objects.all()
    serializer_class = FileSerializer
    # new permissions from permisisons.py added
    permission_classes = [TeamsAndRolesFiles]
    authentication_classes = [JWTAuthentication]

    #  checking for request meta
    def list(self, request, *args, **kwargs):
        # print("=== HEADERS ===")
        # for key, value in request.headers.items():
        #     print(f"{key}: {value}")

        # print("=== META ===")
        # for key, value in request.META.items():
        #     print(f"{key}: {value}")

        # REMEMBER THE TOKEN WAS SAVED INTO THE SESSION INSIDE THE CUSTOM MyTokenObtainPairSerializer
        # print('\n\n=============TOKEN OBTAINED INSIDE A VIEW, THE FILEVIEW================\n')
        # print(request.session.get('token'))
        headers = {
            "Authorization": request.session['token']
        }
        # print('\n\n=============HEADERS================\n')
        # pprint(request.headers)
        # pprint(request.headers['Sec-Fetch-Dest'])
        # https://shafialam.medium.com/django-rest-framework-user-authentication-under-the-hood-http-basic-authentication-671933f06336
        # getting hold of the meta http authorisation 
        # this doesnt work because the request is sent before the method is executed
        # request.META['HTTP_AUTHORIZATION'] = f'Bearer {request.session['token']}'
        # request_token=request.META.get('HTTP_AUTHORIZATION')
        # print(request_token)
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        # checck user from the request
        logged_user=self.request.user
        # use the method inside the team model to the get the accessible files
        return Team.get_accessible_files_based_on_levels(logged_user)

        

    # registering every downloads
    # https://www.django-rest-framework.org/api-guide/viewsets/#marking-extra-actions-for-routing
    # # downloading the file creating the actionlog and modifuication

    # https://www.django-rest-framework.org/api-guide/routers/#routing-for-extra-actions
    # url name will be file-download wjile pattern will be file/pk/download/
    # A viewset may mark extra actions for routing by decorating a method with the @action decorator. These extra actions will be included in the generated routes
    @action(detail=True, methods=['get'], permission_classes=[DownloadPermission])
    def download(self, request, pk=None):
        '''this will create a endpoint at file/pk/download/ where we can download the file. custom logic can be added here'''
        file = self.get_object()

        # we need to compensate for double saves by throttling
        # we check if a download for a instance exists inthe last x milisecond, if no then commence with saving
        now = timezone.now()
        time_window = timedelta(seconds=0.6) 

        # we check if the particaular modif has been made for the file in the last x milisecond
        recent_download_exists = Modification.objects.filter(
            file=file,
            modified_by=request.user if request.user.is_authenticated else User.objects.get(pk=1),
            date_modified__gte=now - time_window
        ).exists()

        # https://docs.djangoproject.com/en/5.1/ref/request-response/
        # https://zetcode.com/django/fileresponse/
        response = FileResponse(open(file.file_data.path,
                                     
        # https://docs.djangoproject.com/en/5.2/topics/files/#using-files-in-models
        # we get the file attributes, path and name. we cant simply pass the file object only, it needs a string
                                      "rb"),
                                      as_attachment=True,)
        # Perform download logic here
        if not recent_download_exists:
            modif = Modification(
                file=file,
                file_name_at_modification=file.file_data.name,
                # get_or_create makes a tuple
                modified_by=request.user if request.user.is_authenticated else User.objects.get(pk=1),
                modified_by_username_at_modification=request.user.username if request.user.is_authenticated else User.objects.get(pk=1).username

            )
            print('print inside the action in view during download')
            # we have a problem here, i believe because of multiple download apps, the download endpoint is hit several times, causing several modif instances to be created
            # to prevent this, we can try to limit the donwload to one instance happeneing only once in a set duration of miliseconds 
            # to diagnose, we can try with deguggerpy and also use curl to hit those endpoints
            # curl -X GET -o curl2.txt http://127.0.0.1:8000/drf/files/1/download/
            # with curl there is no double save
            modif.save()
        # the problem is because we were using free download manager which caused duplicate requests

        # logic for action log
        action_log = ActionLog(
            user=request.user if request.user.is_authenticated else User.objects.get(pk=1),
            username_at_action=request.user.username if request.user.is_authenticated else User.objects.get(pk=1).username,
            action_type='download',
            file=file,
            file_name_at_action=file.file_data.name,
            folder=file.folder if file.folder else None,
            folder_name_at_action=file.folder.name if file.folder else None,
            details="generic action logged"
        )
        action_log.save()
        return response
    
    # https://stackoverflow.com/questions/41110742/django-rest-framework-partial-update
    # As we can see PUT updates the every resource of entire data, 
    # whereas PATCH updates the partial of data.In other words: 
    # We can say PUT replace where PATCH modify.So in this article we are going to look for PATCH method.
    # def update(self, request, *args, **kwargs):
    #     kwargs['partial'] = True
    #     return super().update(request, *args, **kwargs)

    # for updating, we cant do anything about the browsable api throwing a "file_data": [
        # "The submitted data was not a file. Check the encoding type on the form."
    # ]
    # the best way to handle this is via front end

class TagsViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [TeamsAndRolesFiles]
    authentication_classes = [JWTAuthentication]

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [TeamsAndRolesFiles]
    authentication_classes = [JWTAuthentication]


class FolderViewSet(viewsets.ModelViewSet):
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer
    permission_classes = [TeamsAndRolesFolders]
    authentication_classes = [JWTAuthentication]

    # https://stackoverflow.com/questions/72197928/drf-viewset-extra-action-action-serializer-class
    def get_queryset(self):
        # in django (rest framework?), action maybe equivalent to method
        # there can be more actions like ['retrieve', 'update', 'destroy']
        if self.action == 'list':
            return Folder.objects.filter(parent_folder=None)
        return Folder.objects.all()

    # https://www.django-rest-framework.org/api-guide/filtering/
    # https://www.django-rest-framework.org/api-guide/viewsets/#introspecting-viewset-actions
    #  we use queryset to filter our search in this case return the top parent folders only
    # def get_queryset(self):
    #     return Folder.objects.filter(parent_folder=None)  
    # 
    


class ModificationViewSet(viewsets.ModelViewSet):
    queryset = Modification.objects.all()
    serializer_class = ModificationSerializer
    permission_classes = [TeamsAndRolesFiles]
    authentication_classes = [JWTAuthentication]

class ActionLogViewSet(viewsets.ModelViewSet):
    queryset = ActionLog.objects.all()
    serializer_class = ActionLogSerializer
    permission_classes = [TeamsAndRolesFiles]
    authentication_classes = [JWTAuthentication]

    
