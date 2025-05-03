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



class FolderSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Folder
        fields = ['url', 'id', 'name', 'parent']  # Include 'url'


class FileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = File
        fields = ['url', 'id', 'name', 'folder', 'file_type', 'size', 'created_at', 'modified_at']  # Include 'url'


class ModificationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Modification
        fields = ['url', 'id', 'file', 'modified_by', 'date_modified', 'method']  # Include 'url'

class ActionLogSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ActionLog
        fields = ['url', 'id', 'action', 'timestamp', 'user']  # Include 'url'  

class TagSerializer(serializers.HyperlinkedModelSerializer):    
    class Meta:
        model =  Tag
        fields = ['url', 'id', 'name']  # Include 'url'

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']