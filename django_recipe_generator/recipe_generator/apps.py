"""App configuration for the recipe_generator application."""
from django.apps import AppConfig


class RecipeGeneratorConfig(AppConfig):
    """Configuration class for the recipe_generator app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_recipe_generator.recipe_generator'

    def ready(self):
        from . import signals
