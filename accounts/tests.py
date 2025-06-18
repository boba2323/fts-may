from django.test import TestCase

# Create your tests here.

# to check if a token is expired
import jwt
import time
from django.test import TestCase
from django.conf import settings
from jwt.exceptions import ExpiredSignatureError


class JWTTokenTests(TestCase):
    def test_expired_jwt_token_raises_exception(self):
        # Setup: create an expired token
        payload = {
            "some": "data",
            "exp": int(time.time()) - 10  # expired 10 seconds ago
        }

        key = settings.SECRET_KEY
        token = jwt.encode(payload, key, algorithm="HS256")

        # Act & Assert
        with self.assertRaises(ExpiredSignatureError):
            jwt.decode(token, key, algorithms=["HS256"])

