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
    def setUp(self):
        connection.queries_log.clear()

    @classmethod
    def setUpTestData(cls):
        """Set up data for the whole TestCase"""
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
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'recipe_generator/recipe_detail.html'
        )

    def test_view_returns_404_for_invalid_recipe(self):
        response = self.client.get(
            reverse('recipe_detail', kwargs={'pk': 999})
        )
        self.assertEqual(response.status_code, 404)

    def test_context_contains_recipe(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.context['recipe'], self.recipe)

    def test_queryset_prefetch_related(self):
        with self.assertNumQueries(3):
            response = self.client.get(self.detail_url)
            list(response.context['recipe'].ingredients.all())

    def test_back_url_defaults_to_index(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.context['back_url'], self.index_url)

    def test_back_url_from_search_with_referer(self):
        session = self.client.session
        session['came_from_search'] = True
        session.save()

        referer = f"{self.list_url}?q=test"
        response = self.client.get(self.detail_url, HTTP_REFERER=referer)
        self.assertEqual(response.context['back_url'], referer)

    def test_back_url_from_search_without_referer(self):
        session = self.client.session
        session['came_from_search'] = True
        session.save()

        response = self.client.get(self.detail_url)
        self.assertEqual(response.context['back_url'], self.list_url)

    def test_back_url_after_editing(self):
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
        session = self.client.session
        session['came_from_search'] = True
        session['was_editing'] = True
        session.save()

        self.client.get(self.detail_url)
        self.assertIn('came_from_search', self.client.session)
        self.assertNotIn('was_editing', self.client.session)

    def test_malformed_search_query_handled(self):
        session = self.client.session
        session['came_from_search'] = True
        session['was_editing'] = True
        session['search_query'] = "invalid=test&="  # Malformed
        session.save()

        response = self.client.get(self.detail_url)
        # Should fall back to recipe list without crashing
        self.assertEqual(response.context['back_url'], self.list_url)


class RecipeDeleteViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up data for the whole TestCase"""
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
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'recipe_generator/recipe_delete.html'
        )

    def test_successful_deletion(self):
        # Verify the recipe exists first
        self.assertTrue(Recipe.objects.filter(pk=self.recipe.pk).exists())

        response = self.client.post(self.delete_url)

        # Check redirect
        self.assertRedirects(response, self.success_url)

        # Verify recipe was deleted
        self.assertFalse(Recipe.objects.filter(pk=self.recipe.pk).exists())

        self.assertEqual(Ingredient.objects.count(), 2)
        self.assertEqual(Recipe.objects.count(), 0)
        self.assertEqual(RecipeIngredient.objects.count(), 0)

    def test_deletion_of_nonexistent_recipe(self):
        invalid_url = reverse('recipe_delete', kwargs={'pk': 999})  # invalid
        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_success_url(self):
        view = views.RecipeDeleteView()
        view.object = self.recipe
        self.assertEqual(view.get_success_url(), self.success_url)


class RecipeCreateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up data for the whole TestCase"""
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
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipe_generator/create.html')
        self.assertIsInstance(response.context['form'], self.form)
        self.assertIsInstance(response.context['formset'], self.formset)

    def test_successful_creation(self):
        # Verify the recipe doesn't exist
        self.assertEqual(Recipe.objects.count(), 0)
        self.assertEqual(RecipeIngredient.objects.count(), 0)

        response = self.client.post(self.create_url, data=self.valid_data)

        # Verify recipe created
        recipe = Recipe.objects.get(name='test_pizza')
        self.assertRedirects(
            response,
            reverse('recipe_detail', kwargs={'pk': recipe.pk})
        )
        self.assertTrue(Recipe.objects.count(), 1)
        self.assertEqual(RecipeIngredient.objects.count(), 2)

    def test_invalid_post_redisplays_form(self):
        response = self.client.post(
            self.create_url,
            kwargs={
                'name': ' ',
                'instructions': ' ',
                'cooking_time': ' ',
                'ingredients': []
            }
        )

        # Should fall back to recipe create, form is redisplayed with errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipe_generator/create.html')
        self.assertFalse(response.context['form'].is_valid())
        self.assertFalse(response.context['formset'].is_valid())
        self.assertIn('name', response.context['form'].errors)
        self.assertIn('instructions', response.context['form'].errors)
        self.assertIn('cooking_time', response.context['form'].errors)

    def test_duplicate_ingredients(self):
        data = self.valid_data.copy()
        data['recipeingredient_set-1-ingredient'] = self.ingredient1.pk
        response = self.client.post(self.create_url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['formset'].is_valid())


class RecipeEditViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up data for the whole TestCase"""
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
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipe_generator/recipe_edit.html')
        self.assertIsInstance(response.context['form'], self.form)
        self.assertIsInstance(response.context['formset'], self.formset)

    def test_view_returns_404_for_invalid_recipe(self):
        response = self.client.get(reverse('recipe_edit', kwargs={'pk': 999}))
        self.assertEqual(response.status_code, 404)

    def test_successful_edit(self):
        # Verify recipe exist
        self.assertTrue(Recipe.objects.filter(pk=self.recipe.pk).exists())

        response = self.client.post(self.edit_url, data=self.edit_data)

        # Verify recipe changed
        recipe = Recipe.objects.get(pk=self.recipe.pk)
        self.assertRedirects(
            response,
            reverse('recipe_detail', kwargs={'pk': recipe.pk})
        )
        self.assertEqual(recipe.name, 'test_pizza_edit')
        self.assertEqual(recipe.instructions, 'test instructions_edit')

    def test_invalid_post_redisplays_form(self):
        data = {
            'name': '',  # Invalid
            'instructions': '',  # Invalid
            'cooking_time': '',  # Invalid
            'recipeingredient_set-TOTAL_FORMS': '1',
            'recipeingredient_set-INITIAL_FORMS': '0',
            'recipeingredient_set-MIN_NUM_FORMS': '0',
            'recipeingredient_set-MAX_NUM_FORMS': '5',
            'recipeingredient_set-0-ingredient': '',  # Invalid
            'recipeingredient_set-0-quantity': '',  # Invalid
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
        data = self.edit_data.copy()
        data['recipeingredient_set-1-ingredient'] = self.ingredient1.pk
        response = self.client.post(self.edit_url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['formset'].is_valid())


class RecipeListViewTests(TestCase):
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
        cls.list_url = reverse('recipe_list')

    def test_view_returns_correct_template(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipe_generator/recipe_list.html')

    def test_recipe_listing(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.recipe.name)

    def test_context_data_without_search(self):
        response = self.client.get(self.list_url)
        self.assertIn(self.recipe, response.context['recipes'])
        self.assertIn(self.ingredient1, response.context['all_ingredients'])

    def test_context_data_search_filter(self):
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
        data = {'query_ingredients': [self.ingredient1.id]}

        response = self.client.get(self.list_url, data)

        recipes = response.context['recipes']
        recipe = next(r for r in recipes if r.name == self.recipe.name)
        self.assertIn(self.ingredient1.name, recipe.matching_ingredient_names)
        self.assertIn(self.ingredient2.name, recipe.missing_ingredient_names)

    def test_no_matching_recipes(self):
        data = {'query_name': 'nonexistent'}
        response = self.client.get(self.list_url, data)
        self.assertQuerySetEqual(response.context['recipes'], [])

    def test_exclude_ingredient_filter(self):
        data = {'exclude_ingredients': [str(self.ingredient2.id)]}
        response = self.client.get(self.list_url, data)
        recipes = response.context['recipes']
        for r in recipes:
            self.assertNotIn(self.ingredient2, r.ingredients.all())

    def test_name_partial_match(self):
        data = {'query_name': 'Soup'}
        response = self.client.get(self.list_url, data)
        self.assertIn(self.recipe1, response.context['recipes'])
