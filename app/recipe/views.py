"""
view for the recipe api
"""

from rest_framework import (viewsets, mixins)
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (Recipe, Tag, Ingredient)
from recipe.serializers import (
    RecipeSerializers,
    RecipeDetailSerializers,
    TagSerializer,
    IngredientSerializer,
)


class RecipeViewSet(viewsets.ModelViewSet):
    """view for manage recipe API"""
    serializer_class = RecipeDetailSerializers
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        """retrieve query set for authenticated user"""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """return the serializer class for request"""
        if self.action == 'list':
            return RecipeSerializers
        return self.serializer_class

    def perform_create(self, serializer):
        """create a new recipe"""
        serializer.save(user=self.request.user)
        return super().perform_create(serializer)


class BaseRecipeAttrrViewSet(mixins.UpdateModelMixin,
                mixins.DestroyModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    """Base User for recipe attributes"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """filter query set to authenticated user"""
        return self.queryset.filter(user = self.request.user).order_by('-name')


class TagViewSet(BaseRecipeAttrrViewSet):
    """manage tags in the database"""
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrrViewSet):
    """manage tags in the database"""
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()


