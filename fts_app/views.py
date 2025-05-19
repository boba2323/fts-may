from django.shortcuts import render
from django.http import HttpResponse
from django.views import generic
from django.conf import settings

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


User = get_user_model()
class IndexView(generic.TemplateView):
    template_name = "fts_app/index.html"


class Home(APIView):
    # authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        content = {'message': 'Hello, World!'}
        return Response(content)

class UserList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.all()
        # We can also serialize querysets instead of model instances. To do so we simply add a many=True flag to the serializer arguments.
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    # permission_classes = [IsAuthenticated]
    # authentication_classes = [JWTAuthentication]
  

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [AllowAny]

    # registering every downloads
    # https://www.django-rest-framework.org/api-guide/viewsets/#marking-extra-actions-for-routing
    # # downloading the file creating the actionlog and modifuication

    # https://www.django-rest-framework.org/api-guide/routers/#routing-for-extra-actions
    # url name will be file-download wjile pattern will be file/pk/download/
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        '''this will create a endpoint at file/pk/download/ where we can download the file. custom logic can be added here'''
        file = self.get_object()

        # https://docs.djangoproject.com/en/5.1/ref/request-response/
        # https://zetcode.com/django/fileresponse/
        response = FileResponse(open(file.file_data.path,
                                     
        # https://docs.djangoproject.com/en/5.2/topics/files/#using-files-in-models
        # we get the file attributes, path and name. we cant simply pass the file object only, it needs a string
                                      "rb"),
                                      as_attachment=True,)
        # Perform download logic here
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
        return response

class TagsViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class FolderViewSet(viewsets.ModelViewSet):
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer
    permission_classes = [AllowAny]

    # https://stackoverflow.com/questions/72197928/drf-viewset-extra-action-action-serializer-class
    def get_queryset(self):
        # in django, action maybe equivalent to method
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

class ActionLogViewSet(viewsets.ModelViewSet):
    queryset = ActionLog.objects.all()
    serializer_class = ActionLogSerializer

    