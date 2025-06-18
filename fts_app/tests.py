from django.test import TestCase
from django.contrib.auth import get_user, get_user_model

# Create your tests here.
# check for user perms
from permissions.models import Team, TeamMembership, AccessCode
from .models import File, Folder, Modification

User = get_user_model()


