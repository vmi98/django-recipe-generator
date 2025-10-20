from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Recipe, RecipeIngredient
from django_recipe_generator.services.gemini_client import get_unexpected_twist


def generate_ai_twist(recipe_id):
    try:
        recipe_name = Recipe.objects.filter(id=recipe_id
                                            ).values_list('name', flat=True).first()
        ingredients = RecipeIngredient.objects.filter(
            recipe_id=recipe_id).select_related('ingredient').values_list(
                'ingredient__name', flat=True)

        generated_text = get_unexpected_twist(recipe_name, list(ingredients))

        Recipe.objects.filter(id=recipe_id).update(elevating_twist=generated_text)
    except Exception as e:
        error_msg = f"Generation error: {str(e)}"
        Recipe.objects.filter(id=recipe_id).update(elevating_twist=error_msg)


@receiver(post_save, sender=Recipe)
def trigger_ai_twist_on_recipe_change(sender, instance, created, **kwargs):
    """Trigger AI for name changes"""
    # hasattr safety check if not tracker(bulk oper,raw SQL updates)
    if not created and hasattr(instance, 'tracker') and instance.tracker.has_changed('name'):
        generate_ai_twist(instance.id)


@receiver(m2m_changed, sender=Recipe.ingredients.through)
def trigger_ai_twist_on_ingredients_change(sender, instance, action, **kwargs):
    """Trigger AI when ingredients change"""
    if action in ['post_add', 'post_remove', 'post_clear']:
        generate_ai_twist(instance.id)
