"""Test module for API."""
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from django_recipe_generator.recipe_generator.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
)
from django_recipe_generator.recipe_generator.api.serializers import (
    IngredientSerializer,
    RecipeIngredientSerializer,
    RecipeSerializer,
    UserSerializer,
)


class RecipeAPITest(APITestCase):
    """Tests for the CRUD API endpoints including search, and form data."""

    @classmethod
    def setUpTestData(cls):
        """Set up initial test data: user, token, ingredients, and recipes."""
        cls.patcher = patch(
            "django_recipe_generator.recipe_generator.models.get_unexpected_twist",
            return_value={"twist_ingredient": "ingredient",
                          "reason": "reason",
                          "how_to_use": "how_to_use"})
        cls.mock_twist = cls.patcher.start()
        cls.addClassCleanup(cls.patcher.stop)

        cls.user = User.objects.create_user(username='testuser',
                                            password='testpass')
        cls.token = Token.objects.create(user=cls.user)
        cls.ingredient1 = Ingredient.objects.create(name="Salt")
        cls.ingredient2 = Ingredient.objects.create(name="Pepper")
        cls.ingredient3 = Ingredient.objects.create(name="Banana")
        cls.recipe1 = Recipe.objects.create(
            name="test_pizza",
            instructions="test instructions1",
            cooking_time=15,
            owner=cls.user
        )
        cls.recipe2 = Recipe.objects.create(
            name="test_soup",
            instructions="test instructions2",
            cooking_time=40,
            owner=cls.user
        )
        cls.recipe1.ingredients.set([cls.ingredient1, cls.ingredient2])
        cls.recipe2.ingredients.set([cls.ingredient1, cls.ingredient3])

    def setUp(self):
        """Authenticate test client with token before each test."""
        self.client.login(username='testuser', password='testpass')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_filter_search(self):
        """Filter and serach recipes by name and ingredients with exclusions."""
        url = reverse('recipe-filter-search')
        data = {'time_filter': 'standard',
                'query_ingredients': [self.ingredient1.id],
                'query_name': 'test',
                'exclude_ingredients': [self.ingredient2.id]
                }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        recipe = response.data['results'][0]

        self.assertIn('matching_ingredient_names', recipe)
        self.assertEqual(
            recipe['matching_ingredient_names'],
            [self.ingredient1.name]
        )
        self.assertIn('missing_ingredient_names', recipe)
        self.assertEqual(
            recipe['missing_ingredient_names'],
            [self.ingredient3.name]
        )

    def test_list_recipes(self):
        """Test listing all available recipes via GET request."""
        url = reverse('recipe-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Recipe.objects.count(), 2)
        self.assertContains(response, self.recipe1.name)


class AuthAPITest(APITestCase):
    """Tests for authentication-related API endpoints."""

    def test_api_token_auth(self):
        """Test that valid credentials return a valid token."""
        User.objects.create_user(username='testuser',
                                 password='testpass')
        url = reverse('api-token-auth')
        data = {"username": "testuser", "password": "testpass"}

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_register(self):
        """Test user registration via API endpoint."""
        url = reverse('register')
        data = {'username': 'testuser', 'password': 'testpass'}

        self.client.credentials()

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class IngredientSerializerTest(APITestCase):
    """Tests for IngredientSerializer including serialization and validation."""

    def test_serialization(self):
        """Test that an ingredient is serialized correctly."""
        ingredient = Ingredient.objects.create(
            name="Salt", category="seasoning"
        )
        serializer = IngredientSerializer(ingredient)
        expected_data = {
            'id': ingredient.id,
            'name': ingredient.name,
            'category': ingredient.category
        }
        self.assertEqual(serializer.data, expected_data)

    def test_deserialization_valid(self):
        """Test that a valid payload is deserialized into an Ingredient object."""
        data = {'name': 'Sugar', 'category': 'seasoning'}
        serializer = IngredientSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        ingredient = serializer.save()
        self.assertEqual(ingredient.name, data['name'])
        self.assertEqual(ingredient.category, data['category'])

    def test_invalid_name(self):
        """Test that an invalid short name triggers a validation error."""
        data = {'name': 'Su', 'category': 'seasoning'}
        serializer = IngredientSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_duplicants(self):
        """Test that an duplicant ingredient triggers an error."""
        Ingredient.objects.create(
            name="Salt", category="seasoning"
        )
        data = {'name': 'Salt', 'category': 'seasoning'}
        serializer = IngredientSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('unique ', serializer.errors['non_field_errors'][0])


class RecipeIngredientSerializerTest(APITestCase):
    """Tests for RecipeIngredientSerializer serialization and deserialization."""

    def setUp(self):
        """Set up test recipe and ingredient for use in all tests."""
        self.patcher = patch(
            "django_recipe_generator.recipe_generator.models.get_unexpected_twist",
            return_value={"twist_ingredient": "ingredient",
                          "reason": "reason",
                          "how_to_use": "how_to_use"})
        self.mock_twist = self.patcher.start()
        self.addClassCleanup(self.patcher.stop)

        self.user = User.objects.create_user(username='testuser',
                                             password='testpass')
        self.ingredient = Ingredient.objects.create(name="Flour")
        self.recipe = Recipe.objects.create(
            name="test_pizza",
            instructions="test instructions1",
            cooking_time=15,
            owner=self.user
        )

    def test_serialization(self):
        """Test that recipe-ingredient relation is serialized correctly."""
        recipe_ingredient = RecipeIngredient.objects.create(
            ingredient=self.ingredient,
            recipe=self.recipe,
            quantity=2.5
        )
        serializer = RecipeIngredientSerializer(recipe_ingredient)
        expected_data = {
            'ingredient': {
                'id': self.ingredient.id,
                'name': self.ingredient.name
            },
            'quantity': str(recipe_ingredient.quantity)
        }
        self.assertEqual(serializer.data, expected_data)

    def test_deserialization_valid(self):
        """Test that valid data is deserialized into a RecipeIngredient object."""
        data = {
            'ingredient': self.ingredient.id,
            'quantity': 1.0
        }
        serializer = RecipeIngredientSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save(recipe=self.recipe)
        self.assertEqual(obj.ingredient, self.ingredient)
        self.assertEqual(obj.quantity, str(data["quantity"]))

    def test_deserialization_invalid(self):
        """Test that invalid ingredient ID fails validation."""
        data = {
            'ingredient': 9999,
            'quantity': 1.0
        }
        serializer = RecipeIngredientSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('ingredient', serializer.errors)


class RecipeSerializerTest(APITestCase):
    """Test suite for RecipeSerializer:create, update, validate, and context data."""

    def setUp(self):
        """Set up ingredient and recipe with a related RecipeIngredient."""
        self.patcher = patch(
            "django_recipe_generator.recipe_generator.models.get_unexpected_twist",
            return_value={"twist_ingredient": "ingredient",
                          "reason": "reason",
                          "how_to_use": "how_to_use"})
        self.mock_twist = self.patcher.start()
        self.addClassCleanup(self.patcher.stop)

        self.user = User.objects.create_user(username='testuser',
                                             password='testpass')
        self.client.force_authenticate(self.user)  # Authenticate client
        # Build a proper authenticated request for serializer context
        request = self.client.post("/api/recipes/", {}).wsgi_request
        request.user = self.user
        self.context = {"request": request}

        self.ingredient = Ingredient.objects.create(name="Flour")
        self.recipe = Recipe.objects.create(
            name="test_pizza",
            instructions="test instructions1",
            cooking_time=15,
            owner=self.user
        )
        self.recipeingredient = RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient,
            quantity='30',
        )

    def test_serialization(self):
        """Test that recipe with ingredients is serialized correctly."""
        serializer = RecipeSerializer(self.recipe)
        expected_data = {
            "id": self.recipe.id,
            "ingredients": [
                {
                    "ingredient": {
                        "id": self.ingredient.id,
                        "name": self.ingredient.name
                    },
                    "quantity": self.recipeingredient.quantity
                },
            ],
            "name": self.recipe.name,
            "instructions": self.recipe.instructions,
            "cooking_time": self.recipe.cooking_time,
            "owner": self.user.id,
            "elevating_twist": {"twist_ingredient": "ingredient",
                                "reason": "reason",
                                "how_to_use": "how_to_use"}
        }
        self.assertEqual(serializer.data, expected_data)

    def test_deserialization_create(self):
        """Test that valid data creates a new Recipe object."""
        data = {
            "ingredients": [{
                "ingredient": self.ingredient.id,
                "quantity": self.recipeingredient.quantity
            },
            ],
            "name": self.recipe.name,
            "instructions": self.recipe.instructions,
            "cooking_time": self.recipe.cooking_time,
        }
        serializer = RecipeSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        obj = serializer.save()
        self.assertEqual(obj.name, self.recipe.name)

    def test_deserialization_update(self):
        """Test that an existing recipe is updated successfully."""
        data = {
            "ingredients": [{
                "ingredient": self.ingredient.id,
                "quantity": self.recipeingredient.quantity
            },
            ],
            "name": "updated_name",
            "instructions": self.recipe.instructions,
            "cooking_time": self.recipe.cooking_time,
        }
        serializer = RecipeSerializer(instance=self.recipe, data=data,
                                      context=self.context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.name, "updated_name")

    def test_deserialization_invalid_name(self):
        """Test that an invalid short name triggers a validation error."""
        data = {
            "ingredients": [{
                "ingredient": self.ingredient.id,
                "quantity": self.recipeingredient.quantity
            },
            ],
            "name": "BN",
            "instructions": self.recipe.instructions,
            "cooking_time": self.recipe.cooking_time,
        }
        serializer = RecipeSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_deserialization_invalid_cooking_time(self):
        """Test that negative cooking time triggers a validation error."""
        data = {
            "ingredients": [{
                "ingredient": self.ingredient.id,
                "quantity": self.recipeingredient.quantity
            },
            ],
            "name": self.recipe.name,
            "instructions": self.recipe.instructions,
            "cooking_time": -15,
        }
        serializer = RecipeSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('cooking_time', serializer.errors)

    def test_contextual_fields_added(self):
        """Test that contextual fields like matching/missing ingredients are added."""
        self.recipe.matching_ingredient_names = ["Salt"]
        self.recipe.missing_ingredient_names = ["Beef"]

        serializer = RecipeSerializer(
            self.recipe,
            context={"include_ingredient_analysis": True}
        )
        data = serializer.data

        self.assertIn("matching_ingredient_names", data)
        self.assertIn("missing_ingredient_names", data)
        self.assertEqual(data["missing_ingredient_names"], ["Beef"])


class UserSerializerTest(APITestCase):
    """Test suite for UserSerializer: serialize and create users."""

    def test_serialization(self):
        """Test that a user instance is serialized correctly."""
        user = User.objects.create(
            username='test',
            password='testpass'
        )
        serializer = UserSerializer(user)
        expected_data = {
            'username': 'test'
        }
        self.assertEqual(serializer.data, expected_data)

    def test_user_creation(self):
        """Test that a user is created and password is hashed properly."""
        data = {
            'username': 'test',
            'password': 'testpass'
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.username, 'test')
        self.assertTrue(user.check_password('testpass'))
