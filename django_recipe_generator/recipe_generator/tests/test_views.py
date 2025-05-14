"""
Test module for Traditional Django views.
"""
from django.db import connection
from django.test import TestCase
from django.urls import reverse

from django_recipe_generator.recipe_generator import views
from django_recipe_generator.recipe_generator.forms import (
    RecipeForm,
    RecipeIngredientFormSet,
)
from django_recipe_generator.recipe_generator.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
)


class RecipeDetailViewTests(TestCase):
    """Tests for the  retrieving a recipe view."""
    def setUp(self):
        """Clear queries log before each test."""
        connection.queries_log.clear()

    @classmethod
    def setUpTestData(cls):
        """Set up initial test data: ingredients and recipes, urls."""
        cls.ingredient1 = Ingredient.objects.create(name="Salt")
        cls.ingredient2 = Ingredient.objects.create(name="Pepper")
        cls.recipe = Recipe.objects.create(
            name="test_pizza",
            instructions="test instructions",
            cooking_time=15
        )
        cls.recipe.ingredients.set([cls.ingredient1, cls.ingredient2])

        cls.detail_url = reverse('recipe_detail', kwargs={'pk': cls.recipe.pk})
        cls.list_url = reverse('recipe_list')
        cls.index_url = reverse('index')

    def test_view_returns_correct_template(self):
        """Ensure detail view renders the correct template."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'recipe_generator/recipe_detail.html'
        )

    def test_view_returns_404_for_invalid_recipe(self):
        """Test response for a nonexistent recipe ID."""
        response = self.client.get(
            reverse('recipe_detail', kwargs={'pk': 999})
        )
        self.assertEqual(response.status_code, 404)

    def test_context_contains_recipe(self):
        """Ensure the recipe is in the context."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.context['recipe'], self.recipe)

    def test_queryset_prefetch_related(self):
        """
        Check the number of queries with prefetching.
        3 = 2 prefetching queries + 1 django session query
        """
        with self.assertNumQueries(3):
            response = self.client.get(self.detail_url)
            list(response.context['recipe'].ingredients.all())

    def test_back_url_defaults_to_index(self):
        """Check default back_url is index if no session flags."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.context['back_url'], self.index_url)

    def test_back_url_from_search_with_referer(self):
        """Check back_url when session has came_from_search and referer."""
        session = self.client.session
        session['came_from_search'] = True
        session.save()

        referer = f"{self.list_url}?q=test"
        response = self.client.get(self.detail_url, HTTP_REFERER=referer)
        self.assertEqual(response.context['back_url'], referer)

    def test_back_url_from_search_without_referer(self):
        """
        Check back_url fallback to list if came_from_search is set
        but no referer.
        """
        session = self.client.session
        session['came_from_search'] = True
        session.save()

        response = self.client.get(self.detail_url)
        self.assertEqual(response.context['back_url'], self.list_url)

    def test_back_url_after_editing(self):
        """Ensure back_url respects saved search query after editing."""
        session = self.client.session
        session['came_from_search'] = True
        session['was_editing'] = True
        session['search_query'] = "q=test&time_filter=quick"
        session.save()

        response = self.client.get(self.detail_url)
        self.assertEqual(
            response.context['back_url'],
            f"{self.list_url}?q=test&time_filter=quick"
        )

        self.assertNotIn('was_editing', self.client.session)

    def test_session_flags_cleaned_up(self):
        """Test cleanup of session flags like was_editing."""
        session = self.client.session
        session['came_from_search'] = True
        session['was_editing'] = True
        session.save()

        self.client.get(self.detail_url)
        self.assertIn('came_from_search', self.client.session)
        self.assertNotIn('was_editing', self.client.session)

    def test_malformed_search_query_handled(self):
        """Verify malformed search queries do not break view."""
        session = self.client.session
        session['came_from_search'] = True
        session['was_editing'] = True
        session['search_query'] = "invalid=test&="
        session.save()

        response = self.client.get(self.detail_url)
        self.assertEqual(response.context['back_url'], self.list_url)


class RecipeDeleteViewTests(TestCase):
    """Tests deleting recipe view."""
    @classmethod
    def setUpTestData(cls):
        """Set up initial test data: ingredients and recipes, urls."""
        cls.ingredient1 = Ingredient.objects.create(name="Salt")
        cls.ingredient2 = Ingredient.objects.create(name="Pepper")
        cls.recipe = Recipe.objects.create(
            name="test_pizza",
            instructions="test instructions",
            cooking_time=15
        )
        cls.recipe.ingredients.set([cls.ingredient1, cls.ingredient2])
        cls.delete_url = reverse('recipe_delete', kwargs={'pk': cls.recipe.pk})
        cls.success_url = reverse('index')

    def test_view_returns_correct_template(self):
        """Ensure delete view renders correct template."""
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'recipe_generator/recipe_delete.html'
        )

    def test_successful_deletion(self):
        """Test that a recipe is deleted successfully."""
        self.assertTrue(Recipe.objects.filter(pk=self.recipe.pk).exists())

        response = self.client.post(self.delete_url)

        self.assertRedirects(response, self.success_url)
        self.assertFalse(Recipe.objects.filter(pk=self.recipe.pk).exists())
        self.assertEqual(Ingredient.objects.count(), 2)
        self.assertEqual(Recipe.objects.count(), 0)
        self.assertEqual(RecipeIngredient.objects.count(), 0)

    def test_deletion_of_nonexistent_recipe(self):
        """Ensure a 404 is returned for invalid delete URL."""
        invalid_url = reverse('recipe_delete', kwargs={'pk': 999})
        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_success_url(self):
        """Verify success URL after deletion."""
        view = views.RecipeDeleteView()
        view.object = self.recipe
        self.assertEqual(view.get_success_url(), self.success_url)


class RecipeCreateViewTests(TestCase):
    """Tests for creating recipe view."""
    @classmethod
    def setUpTestData(cls):
        """Set up initial test data: ingredients, forms, recipe data, urls."""
        cls.ingredient1 = Ingredient.objects.create(name="Salt")
        cls.ingredient2 = Ingredient.objects.create(name="Pepper")

        cls.create_url = reverse('add_recipe')
        cls.form = RecipeForm
        cls.formset = RecipeIngredientFormSet

        cls.valid_data = {
            'name': 'test_pizza',
            'instructions': 'test instructions',
            'cooking_time': 15,
            'recipeingredient_set-TOTAL_FORMS': '2',
            'recipeingredient_set-INITIAL_FORMS': '0',
            'recipeingredient_set-MIN_NUM_FORMS': '0',
            'recipeingredient_set-MAX_NUM_FORMS': '1000',
            'recipeingredient_set-0-ingredient':
                cls.ingredient1.pk,
            'recipeingredient_set-0-quantity': '200g',
            'recipeingredient_set-1-ingredient':
                cls.ingredient2.pk,
            'recipeingredient_set-1-quantity': '100g'}

    def test_view_returns_correct_template(self):
        """Ensure the creation form renders correctly."""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipe_generator/create.html')
        self.assertIsInstance(response.context['form'], self.form)
        self.assertIsInstance(response.context['formset'], self.formset)

    def test_successful_creation(self):
        """Verify that a valid recipe can be created."""
        self.assertEqual(Recipe.objects.count(), 0)
        self.assertEqual(RecipeIngredient.objects.count(), 0)

        response = self.client.post(self.create_url, data=self.valid_data)

        recipe = Recipe.objects.get(name='test_pizza')
        self.assertRedirects(
            response,
            reverse('recipe_detail', kwargs={'pk': recipe.pk})
        )
        self.assertTrue(Recipe.objects.count(), 1)
        self.assertEqual(RecipeIngredient.objects.count(), 2)

    def test_invalid_post_redisplays_form(self):
        """Ensure invalid input redisplays the form with errors."""
        response = self.client.post(
            self.create_url,
            kwargs={
                'name': ' ',
                'instructions': ' ',
                'cooking_time': ' ',
                'ingredients': []
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipe_generator/create.html')
        self.assertFalse(response.context['form'].is_valid())
        self.assertFalse(response.context['formset'].is_valid())
        self.assertIn('name', response.context['form'].errors)
        self.assertIn('instructions', response.context['form'].errors)
        self.assertIn('cooking_time', response.context['form'].errors)

    def test_duplicate_ingredients(self):
        """
        Test that duplicate ingredients
        in formset cause validation errors.
        """
        data = self.valid_data.copy()
        data['recipeingredient_set-1-ingredient'] = self.ingredient1.pk
        response = self.client.post(self.create_url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['formset'].is_valid())


class RecipeEditViewTests(TestCase):
    """Tests for editing recipe view."""
    @classmethod
    def setUpTestData(cls):
        """Set up initial test data: ingredients,recipe, forms, urls."""
        cls.ingredient1 = Ingredient.objects.create(name="Salt")
        cls.ingredient2 = Ingredient.objects.create(name="Pepper")
        cls.recipe = Recipe.objects.create(
            name="test_pizza",
            instructions="test instructions",
            cooking_time=15
        )
        cls.recipe.ingredients.set([cls.ingredient1, cls.ingredient2])
        cls.edit_data = {
            'name': 'test_pizza_edit',
            'instructions': 'test instructions_edit',
            'cooking_time': 15,
            'recipeingredient_set-TOTAL_FORMS': '2',
            'recipeingredient_set-INITIAL_FORMS': '0',
            'recipeingredient_set-MIN_NUM_FORMS': '0',
            'recipeingredient_set-MAX_NUM_FORMS': '5',
            'recipeingredient_set-0-ingredient':
                cls.ingredient1.pk,
            'recipeingredient_set-0-quantity': '200g',
            'recipeingredient_set-1-ingredient':
                cls.ingredient2.pk,
            'recipeingredient_set-1-quantity': '100g'
        }

        cls.edit_url = reverse('recipe_edit', kwargs={'pk': cls.recipe.pk})
        cls.success_url = reverse(
            'recipe_detail',
            kwargs={'pk': cls.recipe.pk}
        )
        cls.form = RecipeForm
        cls.formset = RecipeIngredientFormSet

    def test_view_returns_correct_template(self):
        """Ensure the edit form renders properly."""
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipe_generator/recipe_edit.html')
        self.assertIsInstance(response.context['form'], self.form)
        self.assertIsInstance(response.context['formset'], self.formset)

    def test_view_returns_404_for_invalid_recipe(self):
        """Return 404 if editing a nonexistent recipe."""
        response = self.client.get(reverse('recipe_edit', kwargs={'pk': 999}))
        self.assertEqual(response.status_code, 404)

    def test_successful_edit(self):
        """Verify a valid edit updates the recipe."""
        self.assertTrue(Recipe.objects.filter(pk=self.recipe.pk).exists())
        response = self.client.post(self.edit_url, data=self.edit_data)

        recipe = Recipe.objects.get(pk=self.recipe.pk)
        self.assertRedirects(
            response,
            reverse('recipe_detail', kwargs={'pk': recipe.pk})
        )
        self.assertEqual(recipe.name, 'test_pizza_edit')
        self.assertEqual(recipe.instructions, 'test instructions_edit')

    def test_invalid_post_redisplays_form(self):
        """Check behavior with invalid edit input."""
        data = {
            'name': '',
            'instructions': '',
            'cooking_time': '',
            'recipeingredient_set-TOTAL_FORMS': '1',
            'recipeingredient_set-INITIAL_FORMS': '0',
            'recipeingredient_set-MIN_NUM_FORMS': '0',
            'recipeingredient_set-MAX_NUM_FORMS': '5',
            'recipeingredient_set-0-ingredient': '',
            'recipeingredient_set-0-quantity': '',
        }
        response = self.client.post(self.edit_url, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipe_generator/recipe_edit.html')
        self.assertFalse(response.context['form'].is_valid())
        self.assertFalse(response.context['formset'].is_valid())
        self.assertIn('name', response.context['form'].errors)
        self.assertIn('instructions', response.context['form'].errors)
        self.assertIn('cooking_time', response.context['form'].errors)

    def test_duplicate_ingredients(self):
        """Ensure duplicate ingredients cause formset validation errors."""
        data = self.edit_data.copy()
        data['recipeingredient_set-1-ingredient'] = self.ingredient1.pk
        response = self.client.post(self.edit_url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['formset'].is_valid())


class RecipeListViewTests(TestCase):
    """Tests for the recipe list view, searching and filtering"""
    @classmethod
    def setUpTestData(cls):
        """Set up initial test data: ingredients, recipes, urls."""
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
        cls.list_url = reverse('recipe_list')

    def test_view_returns_correct_template(self):
        """Ensure list view renders the correct template."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipe_generator/recipe_list.html')

    def test_recipe_listing(self):
        """Check that recipes are listed."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.recipe.name)

    def test_context_data_without_search(self):
        """
        Verify without search and filtering param context contains
        recipes and ingredients.
        """
        response = self.client.get(self.list_url)
        self.assertIn(self.recipe, response.context['recipes'])
        self.assertIn(self.ingredient1, response.context['all_ingredients'])

    def test_context_data_search_filter(self):
        """
        Ensure filters and search params
        are passed correctly to the template context.
        """
        data = {
            'cooking_time': 'standard',
            'query_ingredients': [str(self.ingredient1.id)],
            'query_name': 'pizz',
            'exclude_ingredients': [str(self.ingredient3.id)]
        }

        response = self.client.get(self.list_url, data)
        self.assertEqual(
            response.context['current_cooking_time'],
            data['cooking_time']
        )
        self.assertEqual(
            response.context['query_ingredients'],
            data['query_ingredients']
        )
        self.assertEqual(
            response.context['query_name'],
            data['query_name']
        )
        self.assertEqual(
            response.context['exclude_ingredients'],
            data['exclude_ingredients']
        )

    def test_matching_missing_ingredients(self):
        """Test display of matching and missing ingredients."""
        data = {'query_ingredients': [self.ingredient1.id]}

        response = self.client.get(self.list_url, data)

        recipes = response.context['recipes']
        recipe = next(r for r in recipes if r.name == self.recipe.name)
        self.assertIn(self.ingredient1.name, recipe.matching_ingredient_names)
        self.assertIn(self.ingredient2.name, recipe.missing_ingredient_names)

    def test_no_matching_recipes(self):
        """Ensure no recipes are shown for unmatched queries."""
        data = {'query_name': 'nonexistent'}
        response = self.client.get(self.list_url, data)
        self.assertQuerySetEqual(response.context['recipes'], [])

    def test_exclude_ingredient_filter(self):
        """Verify excluded ingredients are not in results."""
        data = {'exclude_ingredients': [str(self.ingredient2.id)]}
        response = self.client.get(self.list_url, data)
        recipes = response.context['recipes']
        for r in recipes:
            self.assertNotIn(self.ingredient2, r.ingredients.all())

    def test_name_partial_match(self):
        """Ensure name search matches partially."""
        data = {'query_name': 'Soup'}
        response = self.client.get(self.list_url, data)
        self.assertIn(self.recipe1, response.context['recipes'])
