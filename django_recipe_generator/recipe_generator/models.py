from django.db import models
from django.core.validators import MinLengthValidator, MinValueValidator
from django.db.models import Count, ExpressionWrapper, F, IntegerField, Q


class RecipeQuerySet(models.QuerySet):
    def search(self, query_name=None, query_ingredients=None):
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
    def get_queryset(self):
        return RecipeQuerySet(self.model, using=self._db)

    def search(self, query_name=None, query_ingredients=None):
        return self.get_queryset().search(query_name, query_ingredients)

    def filter_recipes(self, time_filter=None, exclude_ingredients=None):
        return self.get_queryset().filter_recipes(time_filter,
                                                  exclude_ingredients)


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)  # e.g., "protein", "vegetable"

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(max_length=200, validators=[MinLengthValidator(3)])
    instructions = models.TextField()
    cooking_time = models.IntegerField(validators=[MinValueValidator(1)])  # in minutes
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient')

    objects = RecipeManager()

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.CharField(max_length=50)

    def __str__(self):
        return self.quantity


class Macro(models.Model):
    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE)
    calories = models.IntegerField()
    protein = models.IntegerField()
    carbs = models.IntegerField()
    fat = models.IntegerField()

    def __str__(self):
        return f"Macros for {self.recipe}"
