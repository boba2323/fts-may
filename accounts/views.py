
# Create your views here.
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .serialiser import UserSerializer
from fts_app.serializers import MyTokenObtainPairSerializer

from rest_framework import generics

# views for obtaining the jwt and store it in HTTPOnly cookie
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()
# # Create your views here.
# # this view is just for creating users without exposing the user list and does not need amy perms
# # https://www.django-rest-framework.org/tutorial/3-class-based-views/
class RegisterView(CreateAPIView):
    authentication_classes = []  # No authentication required for registration
    permission_classes = [AllowAny]  # Allow any user to access this view
    serializer_class = UserSerializer
    

    def post(self, request, format=None):
        serializer_context = {
                'request': request,
            }
        # this is what traceback tells us to do add a context
        # https://stackoverflow.com/questions/34438290/assertionerror-hyperlinkedidentityfield-requires-the-request-in-the-serialize
        serializer = UserSerializer(data=request.data, context=serializer_context)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class CustomTokenObtainPairView(TokenObtainPairView):
    # https://stackoverflow.com/questions/66197928/django-rest-how-do-i-return-simplejwt-access-and-refresh-tokens-as-httponly-coo
# https://medium.com/@cassymyo/how-to-get-token-user-information-using-simple-jwt-django-rest-framework-and-react-js-part-1-af528bab854a
    # first we get the serialiser so we can get the jwt tokens that is attached to the serializer
    def post(self, request, *args, **kwargs):
        # this serialiser needs to be the custom tokenobtainserialiser if we want the token in session
        # for browsable api. when we move to frontend we drop it
        serializer = MyTokenObtainPairSerializer(data=request.data, context={'request': request})
        # get the token

        # https://www.django-rest-framework.org/api-guide/serializers/#raising-an-exception-on-invalid-data

        # automatically raises exception if not true
        serializer.is_valid(raise_exception=True)
        # https://www.django-rest-framework.org/api-guide/serializers/#serializers
        access_token = serializer.validated_data['access']
        refresh_token = serializer.validated_data['refresh']


        # the code below is wrong since we are passing the tokens in the response. remember
        # the tokens are in the validated data since the jwt adds them to the returned data.
        # thus we have to set something else
        # response = Response(serializer.data, status=status.HTTP_201_CREATED)

        
        response = Response(data=serializer.validated_data, status=status.HTTP_200_OK)
        # this is better code
        # response = Response({
        #     "message":"You are loggin in"
        # }, status=status.HTTP_200_OK)
        # https://www.geeksforgeeks.org/python/django-cookie/
        response.set_cookie(key='access',
                            value=access_token,
                            httponly=True,
                            secure=False,
                            samesite='Lax') #false for development)
        response.set_cookie(key='refresh',
                            value=refresh_token,
                            httponly=True,
                            secure=False,
                            samesite='Lax')
        return response


# login basically
# a access token can expire pretty quick. to renew we get a refresh token by htiting the refresh token url endpoint
# in our case we neet to enter the refresh token inside the cookie again just like the access token
class CustomRefreshTokenView(TokenRefreshView):

    def post(self, request, *args, **kwargs):
        # when we hit this endpoint, we may think we need to pass the jwt manually but the frontend does it for us
        # in react { withCredentials: true } // Very important: send cookies!

        # remember that th refresh token is only used to hit the refresh token. we always need the access token
        # to use in auth

        refresh_token = request.COOKIES.get("refresh")
        if refresh_token is None:
            return Response(data=serializer.validated_data)
            return Response({"message":"refresh token not found"})
        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response({'detail': 'Invalid or expired refresh token'}, status=401)

        access_token = serializer.validated_data["access"]
        refresh_token = serializer.validated_data['refresh']

        response = Response({"message": "Access token refreshed"})
        response.set_cookie(
            key='access',
            value=access_token,
            httponly=True,
            secure=False,  # True in production
            samesite='Lax',
            max_age=3600
        )
        # refresh tokens last longer, when they expire we will need the user to log again
        response.set_cookie(
            key='refresh',
            value=refresh_token,
            httponly=True,
            secure=False,  # True in production
            samesite='Lax',
            max_age=3600
        )
        return response


class LoggedUserView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user_serialised = UserSerializer(user, context={'request': request})
        return Response(user_serialised.data)

        
