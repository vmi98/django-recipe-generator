"""
URL configuration for the Recipe Generator API.

Available endpoints:

    GET     /api/recipes/           - List all recipes
    POST    /api/recipes/           - Create a recipe
    GET     /api/recipes/<id>/      - Retrieve a recipe
    PUT     /api/recipes/<id>/      - Update a recipe
    DELETE  /api/recipes/<id>/      - Delete a recipe
    POST    /filter_search/         - Filter/search recipes

    GET     /api/ingredients/       - List all ingredients
    POST    /api/ingredients/       - Create an ingredients
    GET     /api/ingredients/<id>/  - Retrieve an ingredient
    PUT     /api/ingredients/<id>/  - Update an ingredient
    DELETE  /api/ingredients/<id>/  - Delete an ingredient

    GET     /recipe-form-data/      - Retrieve form-related data
                                    (provides available ingredients)
    POST    /api-token-auth/        - Obtain authentication token
    POST    /register/              - Register a new user
"""
from django.urls import path
from django.urls import include
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter
from django_recipe_generator.recipe_generator.api import views


router = DefaultRouter()
router.register(r'recipes', views.RecipeViewSet, basename='recipe')
router.register(r'ingredients', views.IngredientViewSet, basename='ingredient')

urlpatterns = [
    path('', include([
        path('', views.RecipeViewSet.as_view({'get': 'api_root'}),
             name='api-root'),
        path('', include(router.urls)),
        path('api-token-auth/', obtain_auth_token, name='api-token-auth'),
        path('register/', views.RegisterView.as_view(), name='register'),
    ])),
]
