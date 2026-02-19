"""Models.

Models for Recipe, general  and recipe-related ingredients,
macros, manager for search and filter logic.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MinValueValidator
from django.db.models import Count, ExpressionWrapper, F, IntegerField, Q
from model_utils import FieldTracker


class RecipeQuerySet(models.QuerySet):
    """Custom queryset for filtering and searching recipes."""

    def search(self, query_name=None, query_ingredients=None):
        """
        Search recipes by name and/or ingredients.

        Args:
            query_name (str): Partial or full name of the recipe.
            query_ingredients (list): List of ingredient IDs
            for recipe to containg.

        Returns:
            QuerySet: Filtered and annotated recipes.
        """
        qs = self

        if query_name:
            qs = qs.filter(name__icontains=query_name)

        if query_ingredients:
            qs = qs.annotate(
                total=Count('ingredients', distinct=True),
                matching=Count('ingredients',
                               filter=Q(ingredients__id__in=query_ingredients),
                               distinct=True)
            ).annotate(
                missing=ExpressionWrapper(F('total') - F('matching'),
                                          output_field=IntegerField())
            ).filter(matching__gt=0).order_by('missing')

        return qs

    def filter_recipes(self, time_filter=None, exclude_ingredients=None):
        """
        Filter recipes based on time and excluded ingredients.

        Args:
            time_filter (str): One of "quick", "standard", or "long".
            exclude_ingredients (list): Ingredient IDs to exclude.

        Returns:
            QuerySet: Filtered recipes.
        """
        qs = self

        if time_filter == 'quick':
            qs = qs.filter(cooking_time__lt=20)
        elif time_filter == 'standard':
            qs = qs.filter(cooking_time__range=(20, 45))
        elif time_filter == 'long':
            qs = qs.filter(cooking_time__gt=45)

        if exclude_ingredients:
            qs = qs.exclude(ingredients__id__in=exclude_ingredients).distinct()

        return qs


class RecipeManager(models.Manager):
    """Custom manager using RecipeQuerySet."""

    def get_queryset(self):
        return RecipeQuerySet(self.model, using=self._db)

    def search(self, query_name=None, query_ingredients=None):
        """Proxy method for search in RecipeQuerySet."""
        return self.get_queryset().search(query_name, query_ingredients)

    def filter_recipes(self, time_filter=None, exclude_ingredients=None):
        """Proxy method for filter_recipes in RecipeQuerySet."""
        return self.get_queryset().filter_recipes(time_filter,
                                                  exclude_ingredients)


class Ingredient(models.Model):
    """Ingredient model representing food components."""

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)  # e.g., "protein", "vegetable"

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'category'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        """Ingredient representation."""
        return self.name


class Recipe(models.Model):
    """Recipe model with instructions, time, and ingredients."""

    name = models.CharField(max_length=200, validators=[MinLengthValidator(3)])
    instructions = models.TextField()
    cooking_time = models.IntegerField(validators=[MinValueValidator(1)])  # in minutes
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient'
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    elevating_twist = models.JSONField(null=True, blank=True)
    ai_generation_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('generating', 'Generating'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )

    objects = RecipeManager()

    tracker = FieldTracker(fields=['name'])

    class Meta:
        ordering = ['id']

    def __str__(self):
        """Recipe representation."""
        return self.name


class RecipeIngredient(models.Model):
    """Intermediate model for recipe-ingredient relationship."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.CharField(max_length=50)

    def __str__(self):
        """Recipeingredient representation."""
        return self.quantity


class Macro(models.Model):
    """Nutritional information for a recipe."""

    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE)
    calories = models.IntegerField()
    protein = models.IntegerField()
    carbs = models.IntegerField()
    fat = models.IntegerField()

    def __str__(self):
        """Nutritional information representation."""
        return f"Macros for {self.recipe}"
