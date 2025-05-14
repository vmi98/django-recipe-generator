"""
Serializers for recipes, ingredients, and user management.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Recipe, Ingredient, RecipeIngredient


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for basic ingredient data (ID and name)."""
    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """
    Serializer for individual recipe-ingredient relations.

    Provides nested ingredient ID and quantity input/output.
    """
    ingredient = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ['ingredient', 'quantity']

    def to_representation(self, instance):
        """Customize output to show both id and name"""
        representation = super().to_representation(instance)
        ingredient = instance.ingredient
        representation['ingredient'] = {
            'id': ingredient.id,
            'name': ingredient.name
        }
        return representation


class RecipeFormDataSerializer(serializers.Serializer):
    """
    Serializer for initializing recipe creation forms.

    Returns a list of available ingredients.
    """
    ingredients = IngredientSerializer(many=True)


class RecipeSerializer(serializers.ModelSerializer):
    """
    Full serializer for Recipe objects.

    Handles nested ingredient creation and supports contextual flags
    for optional ingredient matching/missing metadata.
    """
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipeingredient_set'
    )

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ['id']

    def to_representation(self, instance):
        """
        Dynamically adds matching/missing ingredient fields
        ONLY when called from filter_search endpoint
        """
        representation = super().to_representation(instance)

        if self.context.get('include_ingredient_analysis', False):
            representation.update(
                {
                    'matching_ingredient_names': getattr(
                        instance,
                        'matching_ingredient_names', []
                    ),
                    'missing_ingredient_names': getattr(
                        instance,
                        'missing_ingredient_names', []
                    ),
                }
            )

        return representation

    def validate_cooking_time(self, value):
        """Ensure cooking time is a positive integer."""
        if value < 0:
            raise serializers.ValidationError("Time must be positive!")
        return value

    def validate_name(self, value):
        """Ensure name is a minimum length."""
        if len(value) < 3:
            raise serializers.ValidationError("Name too short!")
        return value

    def create(self, validated_data):
        """Create a recipe instance with nested ingredients."""
        ingredients_data = validated_data.pop('recipeingredient_set')
        recipe = Recipe.objects.create(**validated_data)

        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                quantity=ingredient_data['quantity']
            )

        return recipe

    def update(self, instance, validated_data):
        """Update a recipe instance, including nested ingredients."""
        ingredients_data = validated_data.pop('recipeingredient_set', [])

        instance.name = validated_data.get('name', instance.name)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        instance.save()

        for ingredient_data in ingredients_data:
            ingredient = ingredient_data['ingredient']
            quantity = ingredient_data['quantity']

            try:
                recipe_ingredient = instance.recipeingredient_set.get(
                    ingredient=ingredient
                )
                recipe_ingredient.quantity = quantity
                recipe_ingredient.save()
            except RecipeIngredient.DoesNotExist:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient,
                    quantity=quantity
                )

        return instance


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user registration using username and password."""
    class Meta:
        model = User
        fields = ('username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        """Create a user with hashed password."""
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user
