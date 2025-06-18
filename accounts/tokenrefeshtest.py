# from datetime import timedelta
# from rest_framework.generics import CreateAPIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from django.contrib.auth import get_user_model
# from .serialiser import UserSerializer

# # views for obtaining the jwt and store it in HTTPOnly cookie
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


# User = get_user_model()
import os
import sys
#  we need this shit since we are running the script from inside the accounts app. thanks chatgpt?
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ftssite.settings")

import django
django.setup()

from django.core.management import call_command

# we try to get the time at which the token expires and if the token is valid or not
import jwt
import datetime
from django.conf import settings
# get the response

payload="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUwMDc0NTUwLCJpYXQiOjE3NTAwNjAxNTAsImp0aSI6IjU2YjdiNzJlZWMyZTRhMjBhNzNiMjUwY2Y3MmM5Y2E4IiwidXNlcl9pZCI6MTV9.USV8a8gWiz7cdjiyEvpH81rHYAXgmSum1DE05jZTaRY"

# the secret is the django secret key thanks for being so fucking obtuse
key = settings.SECRET_KEY

try:
    decoded = jwt.decode(payload, key, algorithms="HS256")
    # https://pyjwt.readthedocs.io/en/stable/usage.html
    # Expiration time is automatically verified in jwt.decode() and raises jwt.ExpiredSignatureError if the expiration time is in the past:
except jwt.ExpiredSignatureError:
    print("expired")

class ApplyFreshToken:
    def get(self, request):
        refresh_t = request.COOKIES.get('refresh')
        access_t = request.COOKIES.get('access')

        try:
            jwt.decode(access_t, key, algorithms="HS256")
        except jwt.ExpiredSignatureError:
            # here we will make a request for new tokens
            try:
                jwt.decode(refresh_t, key, algorithms="HS256")                
            except jwt.ExpiredSignatureError:
                return 