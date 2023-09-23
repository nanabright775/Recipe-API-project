"""
serializers for recipe api
"""

from rest_framework import serializers
from core.models import Recipe


class RecipeSerializers(serializers.ModelSerializer):
    """serializer for recipes"""
    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link']
        read_only_fields=['id']


class RecipeDetailSerializers(RecipeSerializers):
    """serializer for detail recipe view"""
    class Meta(RecipeSerializers.Meta):
        fields = RecipeSerializers.Meta.fields + ['description']
