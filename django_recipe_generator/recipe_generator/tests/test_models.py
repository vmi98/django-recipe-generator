"""Test module for models."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch

from django_recipe_generator.recipe_generator.models import (
    Ingredient,
    Macro,
    Recipe,
)


class RecipeModelTests(TestCase):
    """Test case for Recipe, Ingredient, and Macro model behavior."""

    @classmethod
    def setUpTestData(cls):
        """Set up initial test data: ingredients, recipes, macro."""
        cls.patcher = patch(
            "django_recipe_generator.recipe_generator.models.get_unexpected_twist",
            return_value={"twist_ingredient": "ingredient",
                          "reason": "reason",
                          "how_to_use": "how_to_use"})
        cls.mock_twist = cls.patcher.start()
        cls.addClassCleanup(cls.patcher.stop)  # automatic cleanup after all tests

        cls.ingredient1 = Ingredient.objects.create(name="Salt")
        cls.ingredient2 = Ingredient.objects.create(name="Pepper")
        cls.ingredient3 = Ingredient.objects.create(name="Banana")
        cls.user = User.objects.create_user(username='testuser',
                                            password='testpass')
        cls.recipe = Recipe.objects.create(
            name="test_pizza",
            instructions="test instructions",
            cooking_time=15,
            owner=cls.user
        )
        cls.recipe1 = Recipe.objects.create(
            name="test_soup",
            instructions="test instructions1",
            cooking_time=40,
            owner=cls.user
        )
        cls.recipe.ingredients.set([cls.ingredient1, cls.ingredient2])
        cls.recipe1.ingredients.set([cls.ingredient1, cls.ingredient3])
        cls.macro = Macro.objects.create(
            recipe=cls.recipe,
            calories=300,
            protein=10,
            carbs=50,
            fat=5
        )

    def test_model_creation(self):
        """Test that recipes are created correctly."""
        self.assertEqual(Recipe.objects.count(), 2)
        self.assertEqual(self.recipe.elevating_twist,
                         {"twist_ingredient": "ingredient",
                          "reason": "reason",
                          "how_to_use": "how_to_use"})
        self.assertTrue(self.mock_twist.called)

    def test_str_representation(self):
        """Test string representation of Recipe model."""
        expected_representation = "test_pizza"
        self.assertEqual(str(self.recipe), expected_representation)

    def test_cooking_time_cannot_be_negative(self):
        """Test that negative cooking time raises validation error."""
        self.recipe.cooking_time = -10
        with self.assertRaises(ValidationError):
            self.recipe.full_clean()

    def test_name_cannot_be_short(self):
        """Test that short names raise validation error."""
        self.recipe.name = 'ex'
        with self.assertRaises(ValidationError):
            self.recipe.full_clean()

    def test_recipe_ingredients_relationship(self):
        """Test that recipe has correct ingredients associated."""
        self.assertEqual(self.recipe.ingredients.count(), 2)
        self.assertIn(self.ingredient1, self.recipe.ingredients.all())
        self.assertIn(self.ingredient2, self.recipe.ingredients.all())

    def test_macro_relationship(self):
        """Test that macro is correctly related to recipe."""
        self.assertEqual(self.recipe.macro.calories, self.macro.calories)

    def test_search_by_name(self):
        """Test searching recipes by name returns correct results."""
        results = Recipe.objects.search(query_name="piz")
        self.assertEqual(results.count(), 1)

    def test_search_by_ingredients(self):
        """Test searching recipes by ingredient IDs returns correct results."""
        results = Recipe.objects.search(
            query_ingredients=[
                self.ingredient1.id,
                self.ingredient2.id
            ]
        )
        self.assertEqual(results.count(), 2)
        self.assertEqual(results[0], self.recipe)

    def test_filter_recipes_by_time(self):
        """Test filtering recipes by quick and standard time filters."""
        quick = Recipe.objects.filter_recipes(time_filter="quick")
        standard = Recipe.objects.filter_recipes(time_filter="standard")
        self.assertEqual(quick.count(), 1)
        self.assertEqual(standard.count(), 1)

    def test_filter_exclude(self):
        """Test filtering recipes by excluding ingredients."""
        results = Recipe.objects.filter_recipes(
            exclude_ingredients=[self.ingredient1.id]
        )
        self.assertEqual(results.count(), 0)
