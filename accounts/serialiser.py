from rest_framework import serializers
from django.contrib.auth import get_user_model
User = get_user_model()


class UserSerializer(serializers.HyperlinkedModelSerializer):
    # to show the reverse fields relat4ed to user, we need to explicitly create fields for it. we are doing it
    # here for owned_files. the field must exist in the model
    url = serializers.HyperlinkedIdentityField(view_name='myuser-detail')  # Expects a URL pattern named 'myuser-detail'
    created_access_codes=serializers.HyperlinkedRelatedField(
        many=True, 
        view_name='accesscode-detail', 
        read_only=True
    )  # Reverse relation to AccessCode model

    belongs_to_team = serializers.SerializerMethodField()
    team_access_level = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['url', 'id', 'username', 'email', 'password', 'belongs_to_team', "team_access_level", 'created_access_codes'
                  ,'role']  # Include 'url' field
        # extra_kwargs = {'password': {'write_only': True}}

    # to set hashed password in serialiser. its better than setting it in view or models
  # https://docs.djangoproject.com/en/5.2/ref/contrib/auth/#django.contrib.auth.models.User.set_password

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def get_belongs_to_team(self, user):
        team_membership=user.memberships.first()
        if team_membership and team_membership.team:
            return team_membership.team.name
        return None
    
    def get_team_access_level(self, user):
        user_membership = user.get_team_membership()
        if not user_membership:
            return None
        team_access_level = user_membership.team.level
        return team_access_level

    def get_role(self, user):
        user_membership = user.get_team_membership()
        if user_membership:
            return user_membership.role
        return None