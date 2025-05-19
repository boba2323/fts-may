from rest_framework import serializers
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from .models import File, Folder, Modification, Tag, ActionLog  # Import your models
from rest_framework.reverse import reverse

User = get_user_model()


class UserSerializer(serializers.HyperlinkedModelSerializer):
    # to show the reverse fields relat4ed to user, we need to explicitly create fields for it. we are doing it
    # here for owned_files. the field must exist in the model
    owned_files= serializers.PrimaryKeyRelatedField(many=True ,queryset=File.objects.all()) 
    url = serializers.HyperlinkedIdentityField(view_name='myuser-detail')  # Expects a URL pattern named 'myuser-detail'
    class Meta:
        model = User
        fields = ['url', 'id', 'username', 'email', 'password', 'owned_files']  # Include 'url' field
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

class FolderSerializer(serializers.HyperlinkedModelSerializer):
    # after we add readonly, the subfolders does not need to be added
    subfolders=serializers.HyperlinkedRelatedField(many=True, view_name='folder-detail', read_only=True)
  
    # reverse relation files for the folder
    files=serializers.HyperlinkedRelatedField(many=True, view_name='file-detail', read_only=True)
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
                  'all_files'
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
        request = self.context.get('request')
        # list comprehensiion
        return [
            {
                'id': subfolder.id,
                'name': subfolder.name,
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
                   'folder', 'tags', 'download_url']  

    def get_download_url(self, obj, *args, **kwargs):
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