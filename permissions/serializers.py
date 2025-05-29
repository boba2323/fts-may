from rest_framework import serializers
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from .models import Team, TeamMembership, AccessCode  # Import your models
from rest_framework.reverse import reverse
from pprint import pprint
User = get_user_model()

class TeamSerializer(serializers.HyperlinkedModelSerializer):
    url= serializers.HyperlinkedIdentityField(
        view_name='team-detail',
    )
    class Meta:
        model = Team
        fields = ('id', 'name', 'url', 'name', 'created_at', 'leader', 'workers', 'level' )


class TeamMembershipSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='teammembership-detail',
    )

    class Meta:
        model = TeamMembership
        fields = ('id', 'url', 'team', 'user', 'role')

class AccessCodeSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='accesscode-detail',
    )
    class Meta:
        model = AccessCode
        fields = ( 'url', 'code', 'team', 'created_by', 'created_at', 'expires_at', 'is_active', 'optional_description')