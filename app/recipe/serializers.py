
from dataclasses import field
from pyexpat import model
from core.models import (
    Recipe,
    Tag,
    Ingredient,
)

from rest_framework import serializers

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']

class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)
    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags', 'ingredients']
        read_only_fields = ['id']
    
    def _get_or_create(self, recipe, model , args):
        auth_user = self.context['request'].user
        for arg in args:
            _obj, created = model.objects.get_or_create(user=auth_user, **arg)
            recipe.tags.add(_obj) if model == Tag else  recipe.ingredients.add(_obj)

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create(recipe=recipe, model=Tag, args=tags)
        self._get_or_create(recipe=recipe, model=Ingredient, args=ingredients)
        return recipe
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create(recipe=instance, model=Tag, args=tags)
        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create(recipe=instance, model=Ingredient, args=ingredients)
            
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class RecipeDetailSerializer(RecipeSerializer):
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']