from django.urls import path
from .views import RecipeView

urlpatterns = [
    path('', RecipeView.as_view(), name='recipe'),
]