import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

# from permissions.models import AccessCode
# this will create a cicular import issue
# https://forum.djangoproject.com/t/circular-import-nightmare-how-to-resolve/16722/2
# My solution was to put some quotations around the model name, e.g.
# changing: authors = models.ManyToManyField(User, null=True,blank=True)
# To: authors = models.ManyToManyField(‘User,’ null=True,blank=True)
# the solution



class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
    # need it so we can use it in rbacperms for dj-guardian
    def get_model_name(self):
        return self.__class__.__name__.lower()
    
class Folder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='owned_folders', on_delete=models.SET_NULL, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    parent_folder = models.ForeignKey('self', related_name='subfolders', on_delete=models.CASCADE, null=True, blank=True)
    permissions = models.CharField(max_length=255, default='read')

    # accesscodes
    # for 1 access code, there can be many folders
    # accesscode is within quotation to prevent cicular impport
    access_code = models.ForeignKey('permissions.AccessCode', on_delete=models.SET_NULL, null=True, blank=True, related_name='folders')
    
    
    def __str__(self):
        return self.name
    
    # need it so we can use it in rbacperms for dj-guardian
    def get_model_name(self):
        return self.__class__.__name__.lower()

class File(models.Model):
    file_data = models.FileField(upload_to='user_files/')
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='owned_files', on_delete=models.SET_NULL, null=True, blank=True)
    owner_username_at_creation = models.CharField(max_length=150, blank=True, null=True)  # Store username at creation
    date_created = models.DateTimeField(auto_now_add=True)
    permissions = models.CharField(max_length=255, default='read')
    folder = models.ForeignKey(Folder, related_name='files', on_delete=models.CASCADE, null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='tags')

    # accesscodes
    # for 1 access code, there can be many files
    access_code = models.ForeignKey('permissions.AccessCode', on_delete=models.SET_NULL, null=True, blank=True, related_name='files')

    def __str__(self):
        return self.name
    
    # need it so we can use it in rbacperms for dj-guardian
    def get_model_name(self):
        return self.__class__.__name__.lower()
    
    def save(self, *args, **kwargs):
        if self.owner and not self.owner_username_at_creation:
            self.owner_username_at_creation = self.owner.username
        super().save(*args, **kwargs)

class Modification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(File, related_name='modifications', on_delete=models.SET_NULL, null=True, blank=True)
    file_name_at_modification = models.CharField(max_length=255, blank=True, null=True)  # Store file name at the time
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='modified_files', on_delete=models.SET_NULL, null=True, blank=True)
    modified_by_username_at_modification = models.CharField(max_length=150, blank=True, null=True)  # Store username at the time
    date_modified = models.DateTimeField(auto_now_add=True)
    permissions_at_modification = models.CharField(max_length=255, blank=True, null=True, default='read')
    method = models.CharField(max_length=255, blank=True, null=True, default='downloaded')

    def __str__(self):
        file_name = self.file.name if self.file else self.file_name_at_modification or "Deleted File"
        username = self.modified_by.username if self.modified_by else self.modified_by_username_at_modification or "Deleted User"
        return f"Modification ID: {self.id} of {file_name} by {username} on {self.date_modified}"


    # need it so we can use it in rbacperms for dj-guardian
    def get_model_name(self):
        return self.__class__.__name__.lower()
    

    def save(self, *args, **kwargs):
        print('save inside the modification model')
        if self.file:
            self.file_name_at_modification = self.file.name
        if self.modified_by:
            self.modified_by_username_at_modification = self.modified_by.username
        super().save(*args, **kwargs)



class ActionLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='logged_actions')
    username_at_action = models.CharField(max_length=150, blank=True, null=True)
    action_type = models.CharField(max_length=255)  # e.g., 'upload', 'download', 'view_metadata', 'move', 'delete', 'permission_change', 'folder_create', 'folder_delete'
    file = models.ForeignKey('File', on_delete=models.SET_NULL, null=True, blank=True, related_name='action_logs')
    file_name_at_action = models.CharField(max_length=255, blank=True, null=True)
    folder = models.ForeignKey('Folder', on_delete=models.SET_NULL, null=True, blank=True, related_name='action_logs')
    folder_name_at_action = models.CharField(max_length=255, blank=True, null=True)
    details = models.JSONField(null=True, blank=True)  # To store additional action-specific information



    # need it so we can use it in rbacperms for dj-guardian
    def get_model_name(self):
        return self.__class__.__name__.lower()
    

    def save(self, *args, **kwargs):
        if self.user:
            self.username_at_action = self.user.username
        if self.file:
            self.file_name_at_action = self.file.name
        if self.folder:
            self.folder_name_at_action = self.folder.name
        super().save(*args, **kwargs)

    def __str__(self):
        user_info = f"by {self.username_at_action}" if self.username_at_action else "by System"
        item_info = ""
        if self.file_name_at_action:
            item_info = f"on file '{self.file_name_at_action}'"
        elif self.folder_name_at_action:
            item_info = f"on folder '{self.folder_name_at_action}'"
        return f"[{self.timestamp}] User {user_info} performed '{self.action_type}' {item_info}"