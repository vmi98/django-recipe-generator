from django.urls import path
from django.urls import include
from django.conf import settings
from django_recipe_generator.recipe_generator import views


urlpatterns = [
    # Traditional HTML views
    path('', views.index_view, name='index'),
    path('recipes/new/', views.RecipeCreateView.as_view(), name='add_recipe'),
    path(
        'recipes/<int:pk>/edit',
        views.RecipeEditView.as_view(),
        name='recipe_edit'
    ),
    path(
        'recipes/<int:pk>/delete',
        views.RecipeDeleteView.as_view(),
        name='recipe_delete'
    ),
    path(
        'recipes/<int:pk>/',
        views.RecipeDetailView.as_view(),
        name='recipe_detail'
    ),
    path(
        'recipes/',
        views.RecipeList.as_view(),
        name='recipe_list'),  # Search page/all recipes by default
    # API endpoints
    path('api/', include('django_recipe_generator.recipe_generator.api.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
