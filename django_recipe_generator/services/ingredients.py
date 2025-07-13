from django_recipe_generator.recipe_generator.models import Ingredient


def annotate_recipes(recipes, query_ingredient_ids):
    query_ingredients = set(query_ingredient_ids)

    ingredient_qs = Ingredient.objects.only('id', 'name')

    ingredient_lookup_query = {
        i.id: i.name
        for i in ingredient_qs.filter(id__in=query_ingredients)
    }

    for r in recipes:
        ingredients_ids = {i.id for i in r.ingredients.all()}

        r.matching_ids = list(ingredients_ids & query_ingredients)
        r.missing_ids = list(ingredients_ids - query_ingredients)

        r.matching_ingredient_names = [
            ingredient_lookup_query[i]
            for i in r.matching_ids
        ]
        r.missing_ingredient_names = [
            ing.name
            for ing in r.ingredients.all()
            if ing.id in r.missing_ingredient_ids
        ]
    return recipes
