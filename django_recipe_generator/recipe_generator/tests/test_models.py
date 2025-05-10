from django.core.exceptions import ValidationError
from django.test import TestCase

from django_recipe_generator.recipe_generator.models import (
    Ingredient,
    Macro,
    Recipe,
)


class RecipeModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up data for the whole TestCase"""
        cls.ingredient1 = Ingredient.objects.create(name="Salt")
        cls.ingredient2 = Ingredient.objects.create(name="Pepper")
        cls.ingredient3 = Ingredient.objects.create(name="Banana")
        cls.recipe = Recipe.objects.create(
            name="test_pizza",
            instructions="test instructions",
            cooking_time=15
        )
        cls.recipe1 = Recipe.objects.create(
            name="test_soup",
            instructions="test instructions1",
            cooking_time=40
        )
        cls.recipe.ingredients.set([cls.ingredient1, cls.ingredient2])
        cls.recipe1.ingredients.set([cls.ingredient1, cls.ingredient3])
        Macro.objects.create(
            recipe=cls.recipe,
            calories=300,
            protein=10,
            carbs=50,
            fat=5
        )

    def test_model_creation(self):
        self.assertEqual(Recipe.objects.count(), 2)
        self.assertEqual(self.recipe.name, "test_pizza")

    def test_str_representation(self):
        self.assertEqual(str(self.recipe), "test_pizza")

    def test_cooking_time_cannot_be_negative(self):
        self.recipe.cooking_time = -10
        with self.assertRaises(ValidationError):
            self.recipe.full_clean()

    def test_name_cannot_be_short(self):
        self.recipe.name = 'ex'
        with self.assertRaises(ValidationError):
            self.recipe.full_clean()

    def test_recipe_ingredients_relationship(self):
        self.assertEqual(self.recipe.ingredients.count(), 2)
        self.assertIn(self.ingredient1, self.recipe.ingredients.all())
        self.assertIn(self.ingredient2, self.recipe.ingredients.all())

    def test_macro_relationship(self):
        self.assertEqual(self.recipe.macro.calories, 300)

    def test_search_by_name(self):
        results = Recipe.objects.search(query_name="piz")
        self.assertEqual(results.count(), 1)

    def test_search_by_ingredients(self):
        results = Recipe.objects.search(
            query_ingredients=[
                self.ingredient1.id,
                self.ingredient2.id
            ]
        )
        self.assertEqual(results.count(), 2)
        self.assertEqual(results[0], self.recipe)

    def test_filter_quick_recipes(self):
        quick = Recipe.objects.filter_recipes(time_filter="quick")
        standard = Recipe.objects.filter_recipes(time_filter="standard")
        self.assertEqual(quick.count(), 1)
        self.assertEqual(standard.count(), 1)

    def test_filter_exclude(self):
        results = Recipe.objects.filter_recipes(
            exclude_ingredients=[
                self.ingredient1.id
            ]
        )
        self.assertEqual(results.count(), 0)
