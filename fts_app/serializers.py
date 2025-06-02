from rest_framework import serializers
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from .models import File, Folder, Modification, Tag, ActionLog  # Import your models
from rest_framework.reverse import reverse
from pprint import pprint
User = get_user_model()


class UserSerializer(serializers.HyperlinkedModelSerializer):
    # to show the reverse fields relat4ed to user, we need to explicitly create fields for it. we are doing it
    # here for owned_files. the field must exist in the model
    owned_files= serializers.PrimaryKeyRelatedField(many=True ,queryset=File.objects.all()) 
    url = serializers.HyperlinkedIdentityField(view_name='myuser-detail')  # Expects a URL pattern named 'myuser-detail'
    created_access_codes=serializers.HyperlinkedRelatedField(
        many=True, 
        view_name='accesscode-detail', 
        read_only=True
    )  # Reverse relation to AccessCode model
    class Meta:
        model = User
        fields = ['url', 'id', 'username', 'email', 'password', 'owned_files', 'created_access_codes']  # Include 'url' field
        # extra_kwargs = {'password': {'write_only': True}}

# a user object is created when we call the save method on it.
# https://www.django-rest-framework.org/tutorial/1-serialization/
#  The create() and update() methods define how fully fledged instances are created or modified when calling serializer.save()
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class TagSerializer(serializers.HyperlinkedModelSerializer):   
    url = serializers.HyperlinkedIdentityField(view_name='tag-detail')  
    class Meta:
        model =  Tag
        fields = ['url', 'id', 'name']  # Include 'url'


class FileSerializer(serializers.HyperlinkedModelSerializer):
    # view name in the hyperlink seriliaser field suffix should match the name of thr router in urls.py
    # if viewname is file-detail, then router suffix name should be file, not files
    url = serializers.HyperlinkedIdentityField( read_only=True, view_name='file-detail')  # Expects a URL pattern named 'file-detail'
    tags = TagSerializer(many=True, read_only=True)
    owner_username_at_creation = serializers.PrimaryKeyRelatedField(read_only=True)
    download_url = serializers.SerializerMethodField()
    class Meta:
        model = File
        fields = ['url', 'id', 'file_data', 'name', 'owner', 'owner_username_at_creation', 'date_created','permissions', 
                   'folder', 'tags', 'download_url', "access_code"] 
        
    def validate(self, data):
        '''if we are updating if file already exists, then the same file will be kept because the browser api field says no file chosen'''
        # this is not working since the validation for the type encoding of the file field is done before
        # print("validation")
        # if self.instance.pk:
        #     print("file used from the db to api field")
        #     existing_file = File.objects.filter(pk=self.instance.pk).first()
        #     data['file_data'] = existing_file.file_data

        # for updating, we cant do anything about the browsable api throwing a "file_data": [
        # "The submitted data was not a file. Check the encoding type on the form."
        # ]
    # the best way to handle this is via front end

        return super().validate(data)


    def get_download_url(self, obj, *args, **kwargs):
        # obj is thhe model instance being serialised
        '''this method will link the download to the serializer field download_url. we will use the reverse function to get the url.'''
     
        # obtaining the request object and passing it in the function
        # https://www.geeksforgeeks.org/pass-request-context-to-serializer-from-viewset-in-django-rest-framework/
        request = self.context.get('request')

        # https://www.django-rest-framework.org/api-guide/reverse/
        # we build our url using the reverse function
        relative_download_url=reverse('file-download', args=[obj.id], request=request)

        # https://www.geeksforgeeks.org/get-the-absolute-url-with-domain-in-django/
        # we create the absolute url with with the relative url
        return request.build_absolute_uri(relative_download_url)

class FolderSerializer(serializers.HyperlinkedModelSerializer):
    # after we add readonly, the subfolders does not need to be added
    subfolders=serializers.HyperlinkedRelatedField(many=True, view_name='folder-detail', read_only=True)
  
    # reverse relation files for the folder
    # files=serializers.HyperlinkedRelatedField(many=True, view_name='file-detail', read_only=True)

    # https://stackoverflow.com/questions/14573102/how-do-i-include-related-model-fields-using-django-rest-framework
    # we can do files this way too, by making use of the serliasier we made for file. this way we get the hyperlink and also the extra data
    # remember it is a reverse field 
    files=FileSerializer(many=True, read_only=True)
    # we want all subfolders shown recursively
    all_subfolders = serializers.SerializerMethodField()
    all_files = serializers.SerializerMethodField()
    total_subfolders = serializers.SerializerMethodField()
    class Meta:
        model = Folder
        # subfolders added as a reverse relation
        fields = ['url', 'id', 'owner', 'name', 'date_created', 'parent_folder', 'permissions', 
                  'subfolders',
                  'total_subfolders',
                  'files',
                  'all_subfolders',
                  'all_files', "access_code"
                  ]  # Include 'url'

        # we get the serialiser method by prefixing get_ to the field name
    def get_all_subfolders(self, obj):
        return self.build_subfolder_tree(obj)
    
    # we may also choose to get a flat list of all subfolders
    # def get_all_subfolders(self, obj):
    #     subfolders = obj.subfolders.all()
    #     return [{'id': f.id, 'name': f.name} for f in subfolders]

    def get_total_subfolders(self, obj):
        # we will have to enter every nested folder to get the true count. a challenge
        return self.count_num_of_subfolders(obj)
    
    def count_num_of_subfolders(self, folder):
        count = folder.subfolders.count()
        for subfolder in folder.subfolders.all():
            count += self.count_num_of_subfolders(subfolder)
        return count


    def build_subfolder_tree(self, folder):
        # getting the request body in the serialiser. its not the same as getting the request body in biews
        request = self.context.get('request')
        # list comprehensiion
        return [
            {
                'id': subfolder.id,
                'name': subfolder.name,
                # THIS is how we get to further deeply nested subfolders by a recurring function 
                'all_subfolders': self.build_subfolder_tree(subfolder),
                'files':[ reverse('file-detail', args=[file.id], request=request) for file in subfolder.files.all()]
            }
            for subfolder in folder.subfolders.all()
        ]
    def get_all_files(self, obj):
        return self.build_file_tree(obj)
    
    def build_file_tree(self, folder):
        request = self.context.get('request')
        subfolder_list=[]
        file_list=[]
        if folder.files.all():
            for file in folder.files.all():
                file_info={
                    'id': file.id,
                    'name': file.name,
                    'url': reverse('file-detail', args=[file.id], request=request)
                }
                file_list.append(file_info)
        for subfolder in folder.subfolders.all():
            subfolder_list.append(subfolder)
            for file in subfolder.files.all():
                file_info={
                    'id': file.id,
                    'name': file.name,
                    'url': reverse('file-detail', args=[file.id], request=request),

                }
                file_list.append(file_info)
        return file_list
         
    







class ModificationSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='modification-detail', read_only=True)
    # i guess we dont really need to explicitly build the url for modification detail
    class Meta:
        model = Modification
        fields = ['id', 'url', 'file', 'file_name_at_modification', 'modified_by', 'modified_by_username_at_modification', 'date_modified', 'permissions_at_modification', 'method']
       

class ActionLogSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='actionlog-detail', read_only=True)
    class Meta:
        model = ActionLog
        fields = [ 'id', 'url', 'timestamp', 'user', 'username_at_action', 'action_type', 'file', 'file_name_at_action', 'folder', 'folder_name_at_action', 'details']  # Include 'url'  



class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

# custom jwt serliasier
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
# the settings module exists inside drf in venv
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth.models import AbstractBaseUser, update_last_login
#  File "/home/boba2323/fts-django/.venv/lib/python3.12/site-packages/rest_framework_simplejwt/serializers.py", line 75, in validate
#     refresh = self.get_token(self.user)

from typing import Any, Optional, TypeVar


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    '''this custom class saves the token access to the request session. thus creating a stateful token? the 
        TokenObtainPairSerializer is a base class that we use to build to custom tokenserialiser class
        it has default methods VALIDATE whose source code we found in a traceback that led us to the original source
        in venv. we manipulate the method to extract the request object, get our token and store it in the 
        request object. see that we store the acess not the refresh token. most of the code in the method
        is default code we only add the part that gets the token and stores it in the request session.
        i suppose we use session since it is design to expire after sometime? we can GET BACK TO IT later
    '''
    
# "/home/boba2323/fts-django/.venv/lib/python3.12/site-packages/rest_framework_simplejwt/serializers.py",
# we obtain this code from the module above
    def validate(self, attrs: dict[str, Any]) -> dict[str, str]:
        data = super().validate(attrs)
        request=self.context['request']
        print('*\n\n-------------------the request body----------------------------*\n')
        pprint(request.__dict__)
        print('\n\n============session================\n')
        pprint(request.session)

        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        # lets take a look at the token
        print('\n\n================TOKEN INSIDE VALIDATE METHOD==============\n')
        print(data['access'])
        # lets try adding the token to session and store it there
        request.session['token']=data['access']
        print('\n\n===========PRINTING THE REQUEST SESSION TOKEN=============\n')
        print(request.session['token'])
        # it works now lets see whether we can retrieve it in other views

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return data
    

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # request=context['request']
        # Add custom claims
        # access_token = response.data.get('access')
        
        # # You can store it here if needed
        # print(f"Access token: {access_token}")
        token['name'] = "test_name"
        # ...
        # to check whats going on with the token we can checck these statements
        # __dict__dunder mehtod exposes the attributes and dir() shows us the methods mostly
        # token.access_token gets us the bearer token
        print('*\n\n==================TOKEN==============*\n')
        print(token)
        # pprint(dir(token) )
        # print(token.__dict__)
        # print(token.access_token)
        # print(token.get_token_backend)
        # request = cls.context.get('request')
        # data = request.data
        # session=request.session
        # print(session)
        return token