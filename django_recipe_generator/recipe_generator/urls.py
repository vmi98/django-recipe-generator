"""
URL configuration for the recipe_generator app.

Includes:
- HTML views for recipe management (list, create, edit, delete, detail).
- API endpoints.
- Debug toolbar (only in DEBUG mode).
"""
from django.urls import path
from django.urls import include
from django.conf import settings
from django_recipe_generator.recipe_generator import views


recipe_patterns = [
    path('new/', views.RecipeCreateView.as_view(), name='add_recipe'),
    path(
        '<int:pk>/edit',
        views.RecipeEditView.as_view(),
        name='recipe_edit'
    ),
    path(
        '<int:pk>/delete',
        views.RecipeDeleteView.as_view(),
        name='recipe_delete'
    ),
    path(
        '<int:pk>/',
        views.RecipeDetailView.as_view(),
        name='recipe_detail'
    ),
    path(
        '',
        views.RecipeList.as_view(),
        name='recipe_list'),  # Search page/all recipes by default
]

ingredient_patterns = [
    path('', views.IngredientListView.as_view(), name='ingredient_list'),
    path('new/', views.IngredientCreateView.as_view(), name='add_ingredient'),
    path('<int:pk>/', views.IngredientDetailView.as_view(), name='ingredient_detail'),
    path('<int:pk>/edit', views.IngredientEditView.as_view(), name='ingredient_edit'),
    path('<int:pk>/delete', views.IngredientDeleteView.as_view(), name='ingredient_delete'),
]

urlpatterns = [
    # Traditional HTML views
    path('', views.index_view, name='index'),
    path('recipes/', include(recipe_patterns)),
    path('ingredients/', include(ingredient_patterns)),
    # API endpoints
    path('api/', include('django_recipe_generator.recipe_generator.api.urls')),
]

# Enable Django Debug Toolbar in development mode
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
