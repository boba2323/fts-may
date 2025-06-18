from rest_framework import serializers
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from .models import Team, TeamMembership, AccessCode  # Import your models
from rest_framework.reverse import reverse
from fts_app.serializers import UserSerializer
from pprint import pprint
User = get_user_model()

class TeamMembershipSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='teammembership-detail',
    )

    class Meta:
        model = TeamMembership
        fields = ('id', 'url', 'team', 'user', 'role')

class TeamSerializer(serializers.HyperlinkedModelSerializer):
    url= serializers.HyperlinkedIdentityField(
        view_name='team-detail',
    )
    access_codes= serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='accesscode-detail',
    ) #reverse relationship to access codes in access code model

    # membership_users is a field in team model and not a reverse field in teamembership

    # this below is the reverse relatedd field
    # memberships=serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='teammembership-detail' )

    
    # doing it via this https://stackoverflow.com/questions/14573102/how-do-i-include-related-model-fields-using-django-rest-framework
    # we get the whole Teammembership serialiser info this way
    memberships=TeamMembershipSerializer(many=True, read_only=True)

    # lets attempt to do the same with leader field, we intend to get the full userserialsier structure instead of just a hyperlink
    # leader= UserSerializer()
    # bad idea, it should not be read only since we need to actively fill it. even when its writable, it does not link to existing leaders
    # but makes us create one

    workers=serializers.SerializerMethodField()
    class Meta:
        model = Team
        fields = ('id', 'name', 'url', 'name', 'created_at', 'leader', 'membership_users',
                   'workers',
                     'memberships', 'level', 'access_codes' )

    def get_workers(self, obj):
        # getting the request body in the serialiser. its not the same as getting the request body in biews
        request = self.context.get('request')
        worker_query = obj.get_workers_of_the_team()
        # we turn them in json objects??
        return [{
            'id':query.user.id,
            'user':query.user.username,
            'user_url':reverse('myuser-detail', args=[query.user.id], request=request),
            'team':query.team.name,
            'team_url':reverse('team-detail', args=[query.team.id], request=request),
        } for query in worker_query]
    


class AccessCodeSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='accesscode-detail',
    )
    team_name=serializers.SerializerMethodField()
    class Meta:
        model = AccessCode
        fields = ( 'url', 'code', 'team', 'team_name', 'created_by', 'created_at', 'expires_at', 'is_active', 'optional_description')

    def get_team_name(self, obj):
        if obj.team:
            team=obj.team.name
            return team
        return "No team assigned"
    # https://www.django-rest-framework.org/api-guide/serializers/#field-level-validation
    # we are adding a validation in the field rather than in the object

    def validate_team(self, team_obj):
        team_code = team_obj.access_codes.all().first()
    # https://www.django-rest-framework.org/api-guide/serializers/#accessing-the-initial-data-and-instance
    # use .instance to access serialiaser object
        if self.instance:
            if self.instance.team == team_obj:
                return team_obj
        
        if team_code:
            print(team_code.code)
            raise serializers.ValidationError('This team already has an access code - acccesscode serialiser error')
        
        return team_obj

    # https://www.django-rest-framework.org/api-guide/serializers/#saving-instances
    # def update(self, instance, validated_data):
    #     # team = validated_data['team']
    #     # if team.pk == self.pk:
    #     return instance
