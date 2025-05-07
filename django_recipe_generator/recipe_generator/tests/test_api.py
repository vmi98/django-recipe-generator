from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from django_recipe_generator.recipe_generator.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
)
from django_recipe_generator.recipe_generator.serializers import (
    IngredientSerializer,
    RecipeIngredientSerializer,
    RecipeSerializer,
    UserSerializer,
)


class RecipeAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser',
                                            password='testpass')
        cls.token = Token.objects.create(user=cls.user)
        cls.ingredient1 = Ingredient.objects.create(name="Salt")
        cls.ingredient2 = Ingredient.objects.create(name="Pepper")
        cls.ingredient3 = Ingredient.objects.create(name="Banana")
        cls.recipe1 = Recipe.objects.create(
            name="test_pizza",
            instructions="test instructions1",
            cooking_time=15
        )
        cls.recipe2 = Recipe.objects.create(
            name="test_soup",
            instructions="test instructions2",
            cooking_time=40
        )
        cls.recipe1.ingredients.set([cls.ingredient1, cls.ingredient2])
        cls.recipe2.ingredients.set([cls.ingredient1, cls.ingredient3])

    def setUp(self):
        self.client.login(username='testuser', password='testpass')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_recipe_form_data(self):
        url = reverse('recipe-form-data')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Ingredient.objects.count(), 3)
        self.assertContains(response, self.ingredient1.name)

    def test_filter_search(self):
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
        self.assertEqual(recipe['matching_ingredient_names'], ['Salt'])
        self.assertIn('missing_ingredient_names', recipe)
        self.assertEqual(recipe['missing_ingredient_names'], ['Banana'])

    def test_list_recipes(self):
        url = reverse('recipe-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Recipe.objects.count(), 2)
        self.assertContains(response, self.recipe1.name)


class AuthAPITest(APITestCase):
    def test_api_token_auth(self):
        User.objects.create_user(username='testuser',
                                 password='testpass')
        url = reverse('api-token-auth')
        data = {"username": "testuser", "password": "testpass"}

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_register(self):
        url = reverse('register')
        data = {'username': 'testuser', 'password': 'testpass'}

        # Ensure client is unauthenticated
        self.client.credentials()

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class IngredientSerializerTest(APITestCase):
    def test_serialization(self):
        ingredient = Ingredient.objects.create(name="Salt")
        serializer = IngredientSerializer(ingredient)
        expected_data = {'id': ingredient.id, 'name': 'Salt'}
        self.assertEqual(serializer.data, expected_data)

    def test_deserialization_valid(self):
        data = {'name': 'Sugar'}
        serializer = IngredientSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        ingredient = serializer.save()
        self.assertEqual(ingredient.name, 'Sugar')


class RecipeIngredientSerializerTest(APITestCase):
    def setUp(self):
        self.ingredient = Ingredient.objects.create(name="Flour")
        self.recipe = Recipe.objects.create(
            name="test_pizza",
            instructions="test instructions1",
            cooking_time=15
        )

    def test_serialization(self):
        recipe_ingredient = RecipeIngredient.objects.create(
            ingredient=self.ingredient,
            recipe=self.recipe,
            quantity=2.5
        )
        serializer = RecipeIngredientSerializer(recipe_ingredient)
        expected_data = {
            'ingredient': {
                'id': self.ingredient.id,
                'name': 'Flour'
            },
            'quantity': '2.5'
        }
        self.assertEqual(serializer.data, expected_data)

    def test_deserialization_valid(self):
        data = {
            'ingredient': self.ingredient.id,
            'quantity': 1.0
        }
        serializer = RecipeIngredientSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save(recipe=self.recipe)
        self.assertEqual(obj.ingredient, self.ingredient)
        self.assertEqual(obj.quantity, '1.0')

    def test_deserialization_invalid(self):
        data = {
            'ingredient': 9999,  # assuming this ID doesn't exist
            'quantity': 1.0
        }
        serializer = RecipeIngredientSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('ingredient', serializer.errors)


class RecipeSerializerTest(APITestCase):
    def setUp(self):
        self.ingredient = Ingredient.objects.create(name="Flour")
        self.recipe = Recipe.objects.create(
            name="test_pizza",
            instructions="test instructions1",
            cooking_time=15
        )
        self.recipeingredient = RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient,
            quantity='30'
        )

    def test_serialization(self):
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
            "cooking_time": self.recipe.cooking_time
        }
        self.assertEqual(serializer.data, expected_data)

    def test_deserialization_create(self):
        data = {
            "ingredients": [{
                "ingredient": self.ingredient.id,
                "quantity": self.recipeingredient.quantity
            },
            ],
            "name": self.recipe.name,
            "instructions": self.recipe.instructions,
            "cooking_time": self.recipe.cooking_time
        }
        serializer = RecipeSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        obj = serializer.save()
        self.assertEqual(obj.name, self.recipe.name)

    def test_deserialization_update(self):
        data = {
            "ingredients": [{
                "ingredient": self.ingredient.id,
                "quantity": self.recipeingredient.quantity
            },
            ],
            "name": "updated_name",
            "instructions": self.recipe.instructions,
            "cooking_time": self.recipe.cooking_time
        }
        serializer = RecipeSerializer(instance=self.recipe, data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.name, "updated_name")

    def test_deserialization_invalid_name(self):
        data = {
            "ingredients": [{
                "ingredient": self.ingredient.id,
                "quantity": self.recipeingredient.quantity
            },
            ],
            "name": "BN",  # invalid
            "instructions": self.recipe.instructions,
            "cooking_time": self.recipe.cooking_time
        }
        serializer = RecipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_deserialization_invalid_cooking_time(self):
        data = {
            "ingredients": [{
                "ingredient": self.ingredient.id,
                "quantity": self.recipeingredient.quantity
            },
            ],
            "name": self.recipe.name,
            "instructions": self.recipe.instructions,
            "cooking_time": -15  # invalid
        }
        serializer = RecipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('cooking_time', serializer.errors)

    def test_contextual_fields_added(self):
        # Simulate attributes added in view logic
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
    def test_serialization(self):
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
        data = {
            'username': 'test',
            'password': 'testpass'
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.username, 'test')
        self.assertTrue(user.check_password('testpass'))
