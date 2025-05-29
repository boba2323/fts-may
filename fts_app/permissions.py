from rest_framework import permissions
# from the book

class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
    # Read-only permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the author of a post
        # files and folders have an owner field
        return obj.owner == request.user
    
    # we need more logic for actionlog and modification models