from django.db import models
from django.contrib.auth import get_user_model
import uuid
from django.contrib.auth.models import Permission

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
# =====================x=======================
from django.db import models
from django.contrib.auth import get_user_model
from fts_app.models import Folder, File, Modification, Tag, ActionLog
User = get_user_model()

# ===================exceptions====================
from django.core.exceptions import ObjectDoesNotExist

# =============django guadian========================
from guardian.shortcuts import assign_perm
from guardian.shortcuts import remove_perm

# class Supervisor(models.Model):
#     user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='supervised_teams')
#     team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='supervisors')
#     is_primary = models.BooleanField(default=False)
#     assigned_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('user', 'team')

#     def __str__(self):
#         return f"{self.user.username} supervises {self.team.name}"
# =====================x=========================


class Team(models.Model):
    '''This will be the team that will have a leader and workers. the teams will have
    3 levels, L1, L2  and L3. L1 teams will have full access to all files and folders and perform CRUD operations.
    L2 teams will have access to only limited files and folders, basically only targetted files and
    folders will be assigned to them. depending on roles inside the team, they will have customised CRUD operations
    L3 will have targetted files/folders but only read accesss
    '''
        # these roles are for the entire team as a unit not for inidivduals
    
    LEVEL_CHOICES = [
        ('L1', 'Level 1 - Full Access'),
        ('L2', 'Level 2 - Limited Access'),
        ('L3', 'Level 3 - Read Only'),
    ]
    # since user and team models are m2m we will make a through model called TeamMembership
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # a user can be leader of many teams, but for now we want 1 user to be leader of only 1 team
    # also, 1 user can be part of only 1 team at a time, this is taken care of with constraints in TeamMembership model
    leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='led_teams' )
    # though reverse relation is "teams" its actual team, singular, we have constrained this model
    workers = models.ManyToManyField(
        User,
        through='TeamMembership',

        # https://docs.djangoproject.com/en/5.2/ref/models/fields/#django.db.models.ManyToManyField.through
        # Specifying through_fields=("user", "team") on the ManyToManyField makes 
        # the order of foreign keys on the through model irrelevant. remember we only make the 
        # through_field for the fields on the trhough model. only on the through model
        # this is useful when the through model has multiple foreign keys to the same model.
        # When you have more than one foreign key on an intermediary model to any (or even both) of the models participating in a many-to-many relationship, you must specify through_fields
        through_fields=('team', 'user'),
        related_name='teams'
    )
    level=models.CharField(choices=LEVEL_CHOICES, max_length=2, default='L2')

    def __str__(self):
        return self.name

    def get_accessible_files_based_on_levels(self):
        '''this will return the files that are accessible to the team based on its level.
        L1 teams will have access to all files, L2 teams will have access to only targetted files
        and L3 teams will have read only access to targetted files.'''
        if self.level == 'L1':
            return File.objects.all()
        elif self.level == 'L2' or self.level == 'L3':
            # L2 teams will have access to only targetted files
            # we can use the access codes to filter the files
            if self.access_codes.exists():
                team_access_codes = self.access_codes.all()
                return File.objects.filter(access_code__in=team_access_codes)
            return File.objects.none()
        

    def get_accessible_folders_based_on_levels(self):
        '''this will return the folders that are accessible to the team based on its level.
        L1 teams will have access to all folders, L2 teams will have access to only targetted folders
        and L3 teams will have read only access to targetted folders.'''
        if self.level == 'L1':
            return Folder.objects.all()
        elif self.level == 'L2' or self.level == 'L3':
            # we also have to return only the files and folders that contains the access codes
        # first we find what access codes are available for the team
            if self.access_codes.exists():
                # self=teammembership instance
                # team=team object
                # access_codes = reverse relation from accesscode model
                team_access_codes = self.access_codes.all()
                # https://www.w3schools.com/django/ref_lookups_in.php
                #Get all records where access_codes is one of the values in a list
                # the queryset is already a list
                accessible_folders = Folder.objects.filter(access_code__in=team_access_codes) 
                return accessible_folders
            return Folder.objects.none()
        
    def change_level_of_team(self, new_level:str):
        '''this will change the level of the team and also update the permissions of the team members
        based on the new level.'''
        if new_level not in dict(self.LEVEL_CHOICES).keys():
            raise ValueError(f"Invalid level: {new_level}. Valid levels are: {dict(self.LEVEL_CHOICES).keys()}")
        self.level = new_level
        self.save()
        # we need to update the permissions of the team members based on the new level
        for membership in self.memberships.all():
            membership.apply_permissions_to_team_members()

class TeamMembership(models.Model):
    # choices for roles here will be distributed inside the team amongst the user objects
    ROLE_CHOICES = [
        ('leader', 'Leader'),
        ('worker', 'Worker'),
    ]
    
    # for 1 membership instance we will have 1 user and 1 team and 1 role.
    #  but for 1 user, there can be multiple memberships in reverse and these teammemberships
    # will have a team and role.
    # same for teams, there can be multiple memberships for different users
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        # usage of unique_together
        # https://stackoverflow.com/questions/2201598/how-to-define-two-fields-unique-as-couple
        # https://ilovedjango.com/django/models-and-databases/django-unique-together/
        # Using the constraints features UniqueConstraint is preferred over unique_together. UniqueConstraint provides more functionality than unique_together. unique_together may be deprecated in the future.
        # https://docs.djangoproject.com/en/5.2/ref/models/fields/#django.db.models.ManyToManyField.through_fields
        # unique_together = ('user', 'team')  # prevent duplicate membership


        # this is done so that a user can only be part of one team at a time
        # we didnt use a fk in user model because we would lose the functionality of a
        # trhough model also we want a future scope for m2m
        # https://docs.djangoproject.com/en/5.2/ref/models/constraints/#django.db.models.UniqueConstraint
        # meanign the user wont be repeated more than once in a row, that means
        # he will be assigned a team and role only once
        constraints = [
            models.UniqueConstraint(fields=['user'], name='one_team_per_user',
                                    violation_error_message="A user can only be part of one team at a time.")
        ]

    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.role})"

    def get_accesible_folders(self):
        # we also have to return only the files and folders that contains the access codes
        # first we find what access codes are available for the team
        return self.team.get_accessible_folders_based_on_levels() # Return an empty queryset if no access codes exist
    
    def get_accesible_files(self):
        return self.team.get_accessible_files_based_on_levels()
    
    def set_roles_for_members_based_on_roles(self, object_target:File|Folder):
        '''this will set the roles for the leaders of the team for the given folder.object target is the
        folder or file object for which we are setting the roles. this will be used to set the permissions'''

        # we can use django guardian to assign permissions to the user for the folder
        # https://django-guardian.readthedocs.io/en/stable/userguide/assign/
        # https://django-guardian.readthedocs.io/en/stable/userguide/permissions.html#assigning-permissions-to-users-and-groups
        # # https://django-guardian.readthedocs.io/en/stable/userguide/assign/
        # # at this point, we need to filter permissions only for the accessible folders and files but
        # # Permissions filters for the whole model and not on individuallevel. 
        # # so when we need the Permissions for the accessible folders and files, we cant have that
        # # since Permissions will check for the whole model i.e every model instance that exists

        # now after we check for levels, the granulation of permisions based on 
        # levels will also be handled here
        model_name = object_target.get_model_name()
        if self.team.level == 'L1':
            if self.role == 'leader':
                assign_perm(f"view_{model_name}", self.user, object_target)
                assign_perm(f"add_{model_name}", self.user, object_target)
                assign_perm(f"change_{model_name}", self.user, object_target)
                assign_perm(f"delete_{model_name}", self.user, object_target)
            elif self.role == 'worker':
                assign_perm(f"view_{model_name}", self.user, object_target)
                assign_perm(f"add_{model_name}", self.user, object_target)
                assign_perm(f"change_{model_name}", self.user, object_target)
                assign_perm(f"delete_{model_name}", self.user, object_target)
        elif self.team.level == 'L2':
            # L2 teams will have access to only targetted files and folders
            if self.role == 'leader':
                assign_perm(f"view_{model_name}", self.user, object_target)
                assign_perm(f"add_{model_name}", self.user, object_target)
                assign_perm(f"change_{model_name}", self.user, object_target)
                assign_perm(f"delete_{model_name}", self.user, object_target)
            elif self.role == 'worker':
                assign_perm(f"view_{model_name}", self.user, object_target)
                assign_perm(f"add_{model_name}", self.user, object_target)
        elif self.team.level == 'L3':
            if self.role == 'leader':
                assign_perm(f"view_{model_name}", self.user, object_target)
            elif self.role == 'worker':
                assign_perm(f"view_{model_name}", self.user, object_target)


            # workers should not be able to delete or add folders/files
            # assign_perm('delete_folder', self.user, folder/file)
            # assign_perm('add_folder', self.user, folder/file)


    def fully_remove_old_perms_from_team_members(self, user, object_target:File | Folder):
        '''object_target is the folder or file object for which we are removing the permissions'''
        
        # https://django-guardian.readthedocs.io/en/stable/userguide/remove/
        # dont need to check for permissions, dj-g will do nothing silently if the permission does not exist
        # custom method in the models to get the model name in lowercase
        model_name = object_target.get_model_name()
        remove_perm(f"view_{model_name}", user, object_target)
        remove_perm(f"change_{model_name}", user, object_target) 
        remove_perm(f"delete_{model_name}", user, object_target)
        remove_perm(f"add_{model_name}", user, object_target) 

    def set_add_delete_permissions_to_workers(self, user, object_target:File | Folder):
        # need to get a membership object for the user and the team since its different from self instance
        if not object_target.access_code:
            raise ValueError(f"This { object_target}  does not have an associated team via access code.")
        membership = TeamMembership.objects.get(user=user, team=object_target.access_code.team)
        if not membership:
            raise ValueError(f"This {user} is not a member of the team associated with this file/folder.")
        model_name = object_target.get_model_name()
        if membership.role == 'worker':
            # we will add read and delete permissions to the workers
            assign_perm(f"add_{model_name}", user, object_target)
            assign_perm(f"delete_{model_name}", user, object_target)

    def remove_add_delete_permissions_from_workers(self, user, object_target):
        if not object_target.access_code:
            raise ValueError(f"This { object_target}  does not have an associated team via access code.")
        membership = TeamMembership.objects.get(user=user, team=object_target.access_code.team)
        if not membership:
            raise ValueError(f"This {user} is not a member of the team associated with this file/folder.")
        # custom method in the models to get the model name in lowercase
        model_name = object_target.get_model_name()
        if membership.role == 'worker':
            # we will remove read and delete permissions from the workers
            remove_perm(f"add_{model_name}", user, object_target)
            remove_perm(f"delete_{model_name}", user, object_target)



    def apply_permissions_to_team_members(self):
        '''all permissions will be applied here
        the ones based on levels to the teams
        and the ones based on roles to the team members'''

        accesible_folders = self.get_accesible_folders()
        accessible_files = self.get_accesible_files()
        for folder in accesible_folders:
            self.set_roles_for_members_based_on_roles(folder)

        for file in accessible_files:
            self.set_roles_for_members_based_on_roles(file)

    def save(self, *args, **kwargs):
        if self.team.leader in self.team.workers.all():
            raise ValueError("Leader cannot be a worker in the same team.")
        super().save(*args, **kwargs)
        # https://stackoverflow.com/questions/57452768/how-to-check-if-an-object-is-being-created-for-the-first-time-with-a-custom-prim
        # https://stackoverflow.com/questions/907695/in-a-django-model-custom-save-method-how-should-you-identify-a-new-object
        # https://docs.djangoproject.com/en/5.2/ref/models/instances/#customizing-model-loading
        # we want the perms to be saved to he team members only when it is created for the first time
        # self._state.adding is True creating

        # self._state.adding is False updating
        
        if self._state.adding:
            self.apply_permissions_to_team_members()

    

# we make an attempt build the access codes model.access codes will be used by users to especially l2 teams 
# to access particular files/folders.
class AccessCode(models.Model):
    '''this code will be granted to a team and the team will use it to access the files and folders
    it will attach to a l2 access file and same will be given to a l2 team. the code will be unique for 
    each event.lets name a bunch of files/folders with same accesscode as a teamwork.
    each teamwork will have a unique access code.
    it makes sense for one team to have multiple access codes, but each access code will be unique to a team.
    update: howver due to rising complexity, we will not allow multiple access codes for a team. 1 team will
    have 1 access code at a time and they will  be unique to a teamwork. there will be no overlapping
    files/folders with multiple access codes.
    '''
    #   but what if the teamworks have overlapping files/folders?
    # solution 1 teamwork= 1 unique access code
    code = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_access_codes')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at= models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    optional_description = models.TextField(blank=True, null=True)
    
    # attaching the access code to some file and folder. access codes are uniue to a teamwork
    # instead we attached them via fk field in the folder and file models. this way many 1 code will be shared by
    # many files and folders. this is a many to one relationship.

    # teams will have accesscodes. we have decided that 1 team will have 1 access code at a time. no sharing!! 
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, related_name='access_codes', null=True)

    def __str__(self):
        return f"Access Code: {self.code}"
        # for Team: {self.team.name} by {self.created_by.username if self.team.exists() else 'Unknown'}"


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # request=kwargs.get('request')
        # if request.user:
        #     ac_creator=request.user
        #     if ac_creator.led_teams.exists(): #meaning he is the leader
        #         # if the user is a leader of a team, we can assign the access code to the team
        #         # this will be used to create the access code for the team
        #         self.team = ac_creator.led_teams.first()
        #         self.created_by = ac_creator
        #     else:
        #         raise ValueError("Access code must be created by a team leader.")
        # else:
        #     raise ValueError("Access code must be created by a user.")