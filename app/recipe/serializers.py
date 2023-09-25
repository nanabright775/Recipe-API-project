"""
serializers for recipe api
"""

from rest_framework import serializers
from core.models import (
    Recipe,
    Tag,
)

class TagSerializer(serializers.ModelSerializer):
    """seializer for tags"""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']



class RecipeSerializers(serializers.ModelSerializer):
    """serializer for recipes"""
    tags = TagSerializer(many=True, required=False)
    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags']
        read_only_fields=['id']



    def _get_or_create_tags(self, tags, recipe):
        """handle getting or creating tags as needed"""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user = auth_user,
                **tag,
            )
            recipe.tags.add(tag_obj)



    def create(self, validated_data):
        """create a reipe"""
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        """updating a tag"""

        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance



class RecipeDetailSerializers(RecipeSerializers):
    """serializer for detail recipe view"""
    class Meta(RecipeSerializers.Meta):
        fields = RecipeSerializers.Meta.fields + ['description']

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', [])
        instance = super().update(instance, validated_data)

        # Update the tags
        instance.tags.clear()
        for tag_data in tags_data:
            tag_obj, created = Tag.objects.get_or_create(user=self.context['request'].user, **tag_data)
            instance.tags.add(tag_obj)

        return instance

