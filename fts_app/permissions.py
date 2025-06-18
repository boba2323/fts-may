from rest_framework import permissions
# from the book

from permissions.models import Team, TeamMembership


class RegisterUserPermission(permissions.BasePermission):
    """
    Custom permission to only allow authenticated users to register.
    """
    def has_permission(self, request, view):
        user = request.user
        
        # Allows any one to register but not view the list of users unless aunthenticated
        if not user.is_authenticated:
            return request.method == 'POST'
        if user.supervisor: #full access
            return True
        if  user.is_team_level_L1():
            return True
        if request.method == 'POST':
            if user.is_team_level_L1() and user.is_team_leader():
                return True
            return False
        # For other methods, check if the user is authenticated
        if request.method in permissions.SAFE_METHODS:
            return user.is_authenticated
        return False

class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
    # Read-only permissions are allowed for any request
        if user.is_authenticated and user.supervisor: #full access
            return True
        if  user.is_team_level_L1():
            return True
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the author of a post
        # files and folders have an owner field
        return obj == user
    
    # we need more logic for actionlog and modification models

class TeamsAndRolesFiles(permissions.BasePermission):
    # https://stackoverflow.com/questions/43064417/whats-the-differences-between-has-object-permission-and-has-permission
    # has_permission is called on all HTTP requests whereas, 
    # has_object_permission is called from DRF's method def get_object(self).
    #  Hence, has_object_permission method is available for GET, PUT, DELETE, not for POST requesy
    # so we replicate the check permnission code blocks in each method
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.supervisor: #full access
            return True
        return self._check_permissions(request)
            
       
            
    def has_object_permission(self, request, view, obj):
        if request.user.supervisor: #full access
            return True
        return self._check_permissions(request)
        


    def _check_permissions(self, request):
        user_membership = request.user.memberships.first()
        if not user_membership:
            return False
        user_team_level = user_membership.team.level
        user_role = user_membership.role
        # check for delete, change and add
        if request.method in ["DELETE", "POST"]:
            # user_membership = TeamMembership.objects.get(user=request.user)
            if user_team_level == "L3":
                return False
            elif user_team_level == 'L1':
                return True
            elif user_role == "leader" and user_team_level == 'L2':
                return True
            elif user_role == "worker" and user_team_level == 'L2':
                return False
            
        elif request.method in ["PATCH", "PUT"] :
            if user_team_level == "L3":
                return False
            elif user_team_level == 'L1':
                return True
            elif user_role == "leader" and user_team_level == 'L2':
                return True
            elif user_role == "worker" and user_team_level == 'L2':
                return True
            return False
        
        elif request.method == "GET":
            return True
        
class TeamsAndRolesFolders(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.supervisor: #full access
            return True
        return self._check_permissions(request)
            
       
            
    def has_object_permission(self, request, view, obj):
        if request.user.supervisor: #full access
            return True
        return self._check_permissions(request)
        


    def _check_permissions(self, request):
        user_membership = request.user.memberships.first()
        if not user_membership:
            return False
        user_team_level = user_membership.team.level
        user_role = user_membership.role
        # check for delete, change and add
        if request.method in ["DELETE", "POST"]:
            # user_membership = TeamMembership.objects.get(user=request.user)
            if user_team_level == "L3":
                return False
            elif user_team_level == 'L1':
                return True
            elif user_role == "leader" and user_team_level == 'L2':
                return True
            elif user_role == "worker" and user_team_level == 'L2':
                return False
            
        elif request.method in ["PATCH", "PUT"] :
            if user_team_level == "L3":
                return False
            elif user_team_level == 'L1':
                return True
            elif user_role == "leader" and user_team_level == 'L2':
                return True
            elif user_role == "worker" and user_team_level == 'L2':
                return True
            return False
        
        elif request.method == "GET":
            return True
    

class DownloadPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user_membership = request.user.memberships.first()
        if not user_membership:
            return False
        user_team_level = user_membership.team.level
        if user_team_level == "L3":
                return False
        

