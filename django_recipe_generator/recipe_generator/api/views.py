"""Views (API).

Views for recipe creation, editing, deletion,
listing, and detail display, user registration and token obtaining.
"""
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

from django_recipe_generator.recipe_generator.models import Recipe, Ingredient
from django_recipe_generator.recipe_generator.api.permissions import (
    IsOwnerOrAdmin, IsAdmin)
from django_recipe_generator.recipe_generator.api.serializers import (
    RecipeSerializer,
    IngredientSerializer,
    UserSerializer
)

from django_recipe_generator.services.ingredients import annotate_recipes
from django.db.models import Prefetch
from django.contrib.auth.models import User


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet for listing, creating, and managing recipes."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsOwnerOrAdmin]

    @action(detail=False, methods=['get'])
    def api_root(self, request):
        """Index route at /api/."""
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
        """Filter recipes.

        Filter recipes by name, time, and ingredients, including or excluding
        specific ones. Adds metadata on matching and missing ingredients.

        Args:
            request (Request): The HTTP request containing search
            and filter parameters:
                - query_name (str): Text to match recipe names.
                - time_filter (str): Time-based filter ('quick',
                    'standard', 'long').
                - query_ingredients (list[int]): Ingredient IDs to include.
                - exclude_ingredients (list[int]): Ingredient IDs to exclude.

        Returns:
            Response: Serialized list of filtered recipes, possibly paginated,
            with additional ingredient analysis fields.

        Raises:
            KeyError: If ingredient IDs are invalid or lookup fails.
        """
        query_name = request.data.get('query_name', '')
        time_filter = request.data.get('time_filter', '')
        query_ingredients = set(request.data.get('query_ingredients', []))
        exclude_ingredients = request.data.get('exclude_ingredients', [])

        ingredient_qs = Ingredient.objects.only('id', 'name')

        qs = Recipe.objects.search(
            query_name=query_name,
            query_ingredients=query_ingredients
        ).filter_recipes(
            time_filter=time_filter,
            exclude_ingredients=exclude_ingredients
        ).prefetch_related(Prefetch("ingredients", queryset=ingredient_qs))

        if query_ingredients:
            qs = annotate_recipes(qs, query_ingredients)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context={'include_ingredient_analysis': True}
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            qs,
            many=True,
            context={'include_ingredient_analysis': True}
        )

        return Response(serializer.data)


class IngredientViewSet(viewsets.ModelViewSet):
    """ViewSet for listing, creating, and managing ingredients."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAdmin]


@permission_classes([AllowAny])
class RegisterView(generics.CreateAPIView):
    """View for registering a new user."""

    queryset = User.objects.all()
    serializer_class = UserSerializer


@permission_classes([AllowAny])
class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = 'http://localhost:8000/recipe_generator/accounts/google/login/callback/'
    client_class = OAuth2Client
