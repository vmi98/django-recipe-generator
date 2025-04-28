from rest_framework.response import Response
from django_recipe_generator.recipe_generator.models import Recipe, Ingredient
from django_recipe_generator.recipe_generator.serializers import RecipeSerializer, IngredientSerializer, UserSerializer
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.reverse import reverse
from django.contrib.auth.models import User


   
class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer


    @action(detail=False, methods=['get'])
    def api_root(self, request):
        """Index route at /api/"""
        return Response({
            'recipes_list': {
                'url': reverse('recipe-list', request=request),
                'method': ['GET'],
            },
            'recipes_create': {
                'url': reverse('recipe-list', request=request),
                'method': ['POST'], 
            },
        })
    
    @action(detail=False, methods=['POST'])
    def filter_search(self, request):
        query_name = request.data.get('query_name', '')
        time_filter = request.data.get('time_filter', '')
        query_ingredients = request.data.get('query_ingredients', [])
        exclude_ingredients = request.data.get('exclude_ingredients', [])

        qs = Recipe.objects.search(query_name=query_name,query_ingredients=query_ingredients).filter_recipes(time_filter=time_filter,
            exclude_ingredients=exclude_ingredients).prefetch_related('ingredients')
        
        if query_ingredients:
            ingredient_lookup_query = {i.id: i.name for i in Ingredient.objects.filter(id__in=query_ingredients)}

            for recipe in qs:
                recipe_ingredient_ids = set(recipe.ingredients.values_list('id', flat=True))
                matching_ids = recipe_ingredient_ids.intersection(set(query_ingredients))
                missing_ids = set(recipe_ingredient_ids) - set(query_ingredients)

                ingredient_lookup_recipe = {i.id: i.name for i in Ingredient.objects.filter(id__in=missing_ids)}

                recipe.matching_ingredient_ids = list(matching_ids)
                recipe.missing_ingredient_ids = list(missing_ids)

                recipe.matching_ingredient_names = [ingredient_lookup_query[i] for i in matching_ids]
                recipe.missing_ingredient_names = [ingredient_lookup_recipe[i] for i in missing_ids]

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'include_ingredient_analysis': True})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True, context={'include_ingredient_analysis': True})
        
        return Response(serializer.data)

class RecipeFormDataView(generics.ListAPIView):
    """
    Provides available ingredients needed to initialize a recipe creation form
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

