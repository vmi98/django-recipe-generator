from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Recipe
from .tasks import generate_ai_twist


@receiver(post_save, sender=Recipe)
def trigger_ai_twist_on_recipe_change(sender, instance, created, **kwargs):
    """Trigger AI for name changes"""
    # hasattr safety check if not tracker(bulk oper,raw SQL updates)
    if not created and hasattr(instance, 'tracker') and instance.tracker.has_changed('name'):
        generate_ai_twist.delay(instance.id)


@receiver(m2m_changed, sender=Recipe.ingredients.through)
def trigger_ai_twist_on_ingredients_change(sender, instance, action, **kwargs):
    """Trigger AI when ingredients change"""
    if action in ['post_add', 'post_remove', 'post_clear']:
        generate_ai_twist.delay(instance.id)
