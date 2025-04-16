from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django_recipe_generator.recipe_generator import views
from django.views.generic import TemplateView

    

# Create a router and register our ViewSets with it.
router = DefaultRouter()
router.register(r'recipes', views.RecipeViewSet, basename='recipe')


urlpatterns = [
    path('', TemplateView.as_view(template_name="recipe_generator/index.html"), name='index'), 
    path('recipes/new/', views.RecipeCreateView.as_view(), name='add_recipe'),  # Add new recipe
    #not edited
    #path('recipes/', views.search_recipe, name='recipes_list'),  # Search page/all recipes by default
    #path('', RecipeView.as_view(), name='recipe'), 
    
    path('api/', include(router.urls)),
]

'''
Generated URLs:

GET /api/recipes/ → List all recipes

POST /api/recipes/ → Create a recipe

GET /api/recipes/1/ → Retrieve a recipe

PUT /api/recipes/1/ → Update a recipe

DELETE /api/recipes/1/ → Delete a recipe
'''