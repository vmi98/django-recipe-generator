from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Recipe, Ingredient
from .serializers import RecipeSerializer

class RecipeView(APIView):
    def get(self, request, *args, **kwargs):
        recipe = Recipe.objects.get(id=1)
        serializer = RecipeSerializer(recipe)
        return Response(serializer.data)
