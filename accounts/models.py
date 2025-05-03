from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin

class MyuserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("The Username field must be set")

        user = self.model(
            username=username,
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email , password=None):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email=email,
            password=password,
            username=username,
        )
        user.is_admin = True
        user.is_superuser = True  # Ensure the user is a superuser
        user.save(using=self._db)
        return user
    
class Myuser(AbstractBaseUser, PermissionsMixin):
    # the permissionsmixin is needed to handle the error Myuser' object has no attribute 'get_all_permissions'
    # but apparently that didnt work
    # https://github.com/django/django/blob/5fcfe5361e5b8c9738b1ee4c1e9a6f293a7dda40/django/contrib/auth/models.py#L284
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )
    
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    objects = MyuserManager()

    # username field is required to create a superuser by default
    USERNAME_FIELD = "email"

    # needed to create superuser
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        '''only the admin can return True for all permissions'''
        if self.is_active and self.is_admin:
        # Simplest possible answer: Yes, always
            return True
        return perm in self.get_all_permissions( obj=obj)

    def has_module_perms(self, blogapp):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class Profile(models.Model):
    myuser = models.OneToOneField(Myuser, on_delete=models.CASCADE, primary_key=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    small_status = models.CharField(max_length=150, blank=True)
    profile_desc = models.CharField(max_length=150, blank=True)