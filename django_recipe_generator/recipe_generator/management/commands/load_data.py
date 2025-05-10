import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from django_recipe_generator.recipe_generator.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Macro,
)


class Command(BaseCommand):
    help = 'Load all recipe data (ingredients, recipes, relationships, macros)'

    def handle(self, *args, **options):
        # 1. Load Ingredients
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n=== Loading Ingredients ==="
        ))
        ingredients_path = os.path.join(
            settings.BASE_DIR,
            'django_recipe_generator',
            'recipe_generator',
            'fixtures',
            'ingredients.csv'
        )
        self._load_ingredients(ingredients_path)

        # 2. Load Base Recipes
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n=== Loading Recipes ==="
        ))
        recipes_path = os.path.join(
            settings.BASE_DIR,
            'django_recipe_generator',
            'recipe_generator',
            'fixtures',
            'recipes.csv'
        )
        self._load_recipes(recipes_path)

        # 3. Link Ingredients to Recipes
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n=== Linking Ingredients ==="
        ))
        links_path = os.path.join(
            settings.BASE_DIR,
            'django_recipe_generator',
            'recipe_generator',
            'fixtures',
            'recipe_ingredients.csv'
        )
        self._link_ingredients(links_path)

        # 4. Load Nutritional Macros
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n=== Loading Macros ==="
        ))
        macros_path = os.path.join(
            settings.BASE_DIR,
            'django_recipe_generator',
            'recipe_generator',
            'fixtures',
            'macros.csv'
        )
        self._load_macros(macros_path)

        self.stdout.write(self.style.SUCCESS(
            "\n=== ALL DATA LOADED SUCCESSFULLY ==="
        ))

    def _load_ingredients(self, csv_path):
        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                obj, created = Ingredient.objects.get_or_create(
                    name=row['name'],
                    defaults={'category': row['category']}
                )
                if created:
                    self.stdout.write(f"Created ingredient: {row['name']}")

        self.stdout.write(self.style.SUCCESS(
            f"\nTotal ingredients: {Ingredient.objects.count()}"
        ))

    def _load_recipes(self, csv_path):
        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                obj, created = Recipe.objects.get_or_create(
                    name=row['name'],
                    defaults={
                        'instructions': row['instructions'],
                        'cooking_time': int(row['cooking_time'])
                    }
                )
                if created:
                    self.stdout.write(f"Created recipe: {row['name']}")

        self.stdout.write(self.style.SUCCESS(
            f"\nTotal recipes: {Recipe.objects.count()}"
        ))

    def _link_ingredients(self, csv_path):
        success_count = 0
        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    recipe = Recipe.objects.get(name=row['recipe'])
                    ingredient = Ingredient.objects.get(name=row['ingredient'])

                    obj, created = RecipeIngredient.objects.get_or_create(
                        recipe=recipe,
                        ingredient=ingredient,
                        defaults={'quantity': row['quantity']}
                    )
                    if created:
                        self.stdout.write(
                            f"Linked {ingredient.name} to {recipe.name}"
                        )
                        success_count += 1
                except Recipe.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️ Recipe not found: {row['recipe']}"
                    ))
                except Ingredient.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️ Ingredient not found: {row['ingredient']}"
                    ))

        self.stdout.write(self.style.SUCCESS(
            f"\nCreated {success_count} recipe-ingredient relationships"
        ))

    def _load_macros(self, csv_path):
        success_count = 0
        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    recipe = Recipe.objects.get(name=row['recipe'])
                    obj, created = Macro.objects.get_or_create(
                        recipe=recipe,
                        defaults={
                            'calories': int(row['calories']),
                            'protein': int(row['protein']),
                            'carbs': int(row['carbs']),
                            'fat': int(row['fat'])
                        }
                    )
                    if created:
                        self.stdout.write(f"Added macros for {recipe.name}")
                        success_count += 1
                except Recipe.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️ Recipe not found: {row['recipe']}"
                    ))

        self.stdout.write(self.style.SUCCESS(
            f"\nLoaded macros for {success_count} recipes"
        ))
