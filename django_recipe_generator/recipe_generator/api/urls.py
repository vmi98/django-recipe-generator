from django.urls import path
from django.urls import include
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter
from django_recipe_generator.recipe_generator.api import views


router = DefaultRouter()
router.register(r'recipes', views.RecipeViewSet, basename='recipe')

urlpatterns = [
    path('', include([
        path('', views.RecipeViewSet.as_view({'get': 'api_root'}),
             name='api-root'),
        path('', include(router.urls)),
        path('recipe-form-data/', views.RecipeFormDataView.as_view(),
             name='recipe-form-data'),
        path('api-token-auth/', obtain_auth_token, name='api-token-auth'),
        path('register/', views.RegisterView.as_view(), name='register'),
    ])),
]

'''
Generated URLs:

GET /api/recipes/ → List all recipes

POST /api/recipes/ → Create a recipe

GET /api/recipes/1/ → Retrieve a recipe

PUT /api/recipes/1/ → Update a recipe

DELETE /api/recipes/1/ → Delete a recipe

+

POST /filter_search/ → Filter/serach recipe
'''
