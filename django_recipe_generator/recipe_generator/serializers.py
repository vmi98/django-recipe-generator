from rest_framework import serializers
from .models import Recipe, Ingredient, RecipeIngredient
from django.contrib.auth.models import User


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']

class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    
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
    """Main serializer for the form initialization endpoint"""
    ingredients = IngredientSerializer(many=True)

    
class RecipeSerializer(serializers.ModelSerializer):
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
        
        # Check for the context flag from filter_search
        if self.context.get('include_ingredient_analysis', False):
            representation.update({
                'matching_ingredient_names': getattr(instance, 'matching_ingredient_names', []),
                'missing_ingredient_names': getattr(instance, 'missing_ingredient_names', []),
            })
        
        return representation

    def validate_cooking_time(self, value):
        if value < 0:
            raise serializers.ValidationError("Time must be positive!")
        return value
    
    def validate_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Name too short!")
        return value
    
    def create(self, validated_data):
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
        # Extract ingredients data
        ingredients_data = validated_data.pop('recipeingredient_set', [])

        # Update basic fields of the recipe
        instance.name = validated_data.get('name', instance.name)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        instance.save()

        # Update or create related RecipeIngredient objects
        for ingredient_data in ingredients_data:
            ingredient = ingredient_data['ingredient']
            quantity = ingredient_data['quantity']

            # Check if the RecipeIngredient already exists (match by recipe and ingredient)
            try:
                recipe_ingredient = instance.recipeingredient_set.get(ingredient=ingredient)
                # Update the quantity
                recipe_ingredient.quantity = quantity
                recipe_ingredient.save()
            except RecipeIngredient.DoesNotExist:
                # If it doesn't exist, create a new one
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient,
                    quantity=quantity
                )

        return instance
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user
