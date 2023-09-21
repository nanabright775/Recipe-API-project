"""
user view for the user api
"""

from rest_framework import generics
from user.serielizers import UserSerielizers


# Create your views here.

class CreateUserView(generics.CreateAPIView):
    """create a new user in the system"""
    serializer_class = UserSerielizers