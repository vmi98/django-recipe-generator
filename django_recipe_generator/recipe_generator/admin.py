"""
Admin configuration for the recipe_generator application.

Registers models with the Django admin interface and customizes
their display and behavior within the admin panel.
"""
from django.contrib import admin
from .models import Ingredient, Recipe, RecipeIngredient, Macro


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Admin interface options for the Ingredient model."""

    list_display = ('name', 'category')
    search_fields = ('name',)
    list_filter = ('category',)


class RecipeIngredientInline(admin.TabularInline):
    """
    Inline editing configuration for RecipeIngredient model.

    Allows RecipeIngredient instances to be edited directly within
    the Recipe admin interface.
    """

    model = RecipeIngredient
    extra = 1  # Number of empty forms to show
    autocomplete_fields = ['ingredient']
    fields = ('ingredient', 'quantity')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin interface options for the Recipe model."""

    inlines = [RecipeIngredientInline]
    list_display = ('name', 'cooking_time')


@admin.register(Macro)
class MacroAdmin(admin.ModelAdmin):
    """Admin interface options for the Macro model."""

    list_display = ('recipe', 'calories', 'protein', 'carbs', 'fat')
