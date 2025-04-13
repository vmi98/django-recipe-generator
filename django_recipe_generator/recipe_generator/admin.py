from django.contrib import admin
from .models import Ingredient, Recipe, RecipeIngredient, Macro

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name',)
    list_filter = ('category',)

class RecipeIngredientInline(admin.TabularInline):  # For inline editing
    model = RecipeIngredient
    extra = 1  # Number of empty forms to show
    # Optional: show ingredient names in dropdown
    autocomplete_fields = ['ingredient']

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = ('name', 'cooking_time')

@admin.register(Macro)
class MacroAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'calories', 'protein', 'carbs', 'fat')



