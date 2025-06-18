# ftssite/middleware/refresh_jwt.py (you can adjust the path)

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.http import JsonResponse

# https://docs.djangoproject.com/en/5.1/topics/http/middleware/#writing-your-own-middleware
# this is just simple middleware code from the docs 
class RefreshJWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.secret_key = settings.SECRET_KEY

    def __call__(self, request):
        access_token = request.COOKIES.get('access')
        refresh_token = request.COOKIES.get('refresh')

        if access_token:
            try:
                jwt.decode(access_token, self.secret_key, algorithms=["HS256"])
            except ExpiredSignatureError:
                # Try to refresh using the refresh token
                if refresh_token:
                    try:
                        jwt.decode(refresh_token, self.secret_key, algorithms=["HS256"])

                        # It's valid, generate new access token
                        # https://django-rest-framework-simplejwt.readthedocs.io/en/latest/rest_framework_simplejwt.html?utm_source=chatgpt.com#rest_framework_simplejwt.tokens.RefreshToken
                        # Returns an access token created from this refresh token. Copies all claims present
                        #  in this refresh token to the new access token except those claims listed in the 
                        # no_copy_claims attribute.
                        refresh = RefreshToken(refresh_token)
                        new_access_token = str(refresh.access_token)

                        # Temporarily attach it to request object for downstream use
                        request.new_access_token = new_access_token

                    except ExpiredSignatureError:
                        return JsonResponse({"detail": "Refresh token expired"}, status=401)
                    except InvalidTokenError:
                        return JsonResponse({"detail": "Invalid refresh token"}, status=401)
                else:
                    return JsonResponse({"detail": "Access token expired, refresh token missing"}, status=401)
            except InvalidTokenError:
                return JsonResponse({"detail": "Invalid access token"}, status=401)

        # Get the response (continue to view)
        response = self.get_response(request)

        # If new access token was set, include it in cookies
        if hasattr(request, "new_access_token"):
            response.set_cookie("access", request.new_access_token, httponly=True)

        return response


# now add it to the settings