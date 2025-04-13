from rest_framework import serializers
from .models import Recipe, Ingredient

class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = '__all__'

    def validate_cooking_time(self, value):
        if value < 0:
            raise serializers.ValidationError("Time must be positive!")
        return value