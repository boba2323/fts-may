from rest_framework import serializers
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from .models import File, Folder, Modification, Tag, ActionLog  # Import your models


User = get_user_model()


class UserSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='myuser-detail')  # Expects a URL pattern named 'myuser-detail'
    class Meta:
        model = User
        fields = ['url', 'id', 'username', 'email', 'password']  # Include 'url' field
        # extra_kwargs = {'password': {'write_only': True}}

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
    url = serializers.HyperlinkedIdentityField(view_name='tags-detail')  
    class Meta:
        model =  Tag
        fields = ['url', 'id', 'name']  # Include 'url'

class FolderSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Folder
        fields = ['url', 'id', 'name', 'parent']  # Include 'url'


class FileSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(many=True, read_only=True, view_name='file-detail')  # Expects a URL pattern named 'file-detail'
    tags = TagSerializer(many=True, read_only=True)
    class Meta:
        model = File
        fields = ['url', 'id', 'file_data', 'name', 'owner','owner_username_at_creation','date_created','permissions', 
                   'folder', 'tags']  # Include 'url'


class ModificationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Modification
        fields = ['id', 'file', 'file_name_at_modification', 'modified_by', 'modified_by_username_at_modification', 'date_modified', 'permissions_at_modification', 'method']
       

class ActionLogSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ActionLog
        fields = [ 'id', 'timestamp', 'user', 'username_at_action', 'action_type', 'file', 'file_name_at_action', 'folder', 'folder_name_at_action', 'details']  # Include 'url'  



class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']