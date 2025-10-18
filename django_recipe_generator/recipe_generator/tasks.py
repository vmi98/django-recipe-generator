from celery import shared_task
from django_recipe_generator.services.gemini_client import get_unexpected_twist
from .models import Recipe, RecipeIngredient


@shared_task
def generate_ai_twist(recipe_id):
    try:
        Recipe.objects.filter(id=recipe_id).update(
            ai_generation_status='generating'
        )
        recipe_name = Recipe.objects.filter(id=recipe_id
                                            ).values_list('name', flat=True).first()

        ingredients = RecipeIngredient.objects.filter(
            recipe_id=recipe_id).select_related('ingredient').values_list(
                'ingredient__name', flat=True)

        generated_text = get_unexpected_twist(recipe_name, list(ingredients))

        Recipe.objects.filter(id=recipe_id).update(elevating_twist=generated_text,
                                                   ai_generation_status='completed')
    except Exception as e:
        error_msg = f"Generation error: {str(e)}"
        Recipe.objects.filter(id=recipe_id).update(elevating_twist=error_msg,
                                                   ai_generation_status='failed')
