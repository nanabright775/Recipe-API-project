"""
user view for the user api
"""

from rest_framework import generics, authentication, permissions
from user.serielizers import (UserSerielizers, AuthTokenSerilizer)
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

# Create your views here.

class CreateUserView(generics.CreateAPIView):
    """create a new user in the system"""
    serializer_class = UserSerielizers

class CreateTokenView(ObtainAuthToken):
    """create a new auth token for user"""
    serializer_class = AuthTokenSerilizer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """manage authenticated user"""
    serializer_class = UserSerielizers
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """retrieve and return authenticated user"""
        return self.request.user