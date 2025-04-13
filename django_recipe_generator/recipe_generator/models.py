from django.db import models

class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)  # e.g., "protein", "vegetable"

class Recipe(models.Model):
    name = models.CharField(max_length=200)
    instructions = models.TextField()
    cooking_time = models.IntegerField()  # in minutes
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient')

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.CharField(max_length=50)  # e.g., "1 cup"

class Macro(models.Model):
    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE)
    calories = models.IntegerField()
    protein = models.IntegerField()  # in grams
    carbs = models.IntegerField()
    fat = models.IntegerField()
