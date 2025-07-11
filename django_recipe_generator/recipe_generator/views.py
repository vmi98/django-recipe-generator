"""
Views (Traditional Djangoapp) for recipe creation, editing, deletion,
listing, and detail display.

Handles form processing, session tracking, and filtering logic.
"""

from django.shortcuts import render, redirect
from urllib.parse import parse_qs, urlencode

from django.db.models import Prefetch
from django.urls import reverse, reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView

from .forms import RecipeForm, RecipeIngredientFormSet
from .models import Ingredient, Recipe, RecipeIngredient

ALLOWED_SEARCH_PARAMS = [
    'q',
    'query_ingredients',
    'time_filter',
    'exclude_ingredients',
    'query_name'
]


class RecipeCreateView(CreateView):
    """View for creating a new recipe with inline ingredients."""
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipe_generator/create.html'

    def get(self, request, *args, **kwargs):
        """Display empty form and formset for recipe creation."""
        form = self.form_class()
        formset = RecipeIngredientFormSet()
        return render(
            request,
            self.template_name,
            {'form': form, 'formset': formset}
        )

    def post(self, request, *args, **kwargs):
        """Handle form submission and create recipe with ingredients."""
        form = self.form_class(request.POST)
        formset = RecipeIngredientFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            recipe = form.save()
            formset.instance = recipe
            formset.save()

            return redirect(reverse('recipe_detail', kwargs={'pk': recipe.pk}))

        return render(
            request,
            self.template_name,
            {'form': form, 'formset': formset}
        )


class RecipeDetailView(DetailView):
    """Display full details of a recipe with its ingredients."""
    model = Recipe
    template_name = 'recipe_generator/recipe_detail.html'
    context_object_name = 'recipe'

    def get_queryset(self):
        """Optimize ingredient fetching with prefetch."""
        return super().get_queryset().prefetch_related(
            Prefetch(
                'recipeingredient_set',
                queryset=RecipeIngredient.objects.select_related('ingredient')
            )
        )

    def get_context_data(self, **kwargs):
        """
        Inject back URL logic (depend on the previous page)
        for navigation context.
        """
        context = super().get_context_data(**kwargs)
        request = self.request

        if request.session.get('came_from_search'):
            if request.session.get('was_editing'):
                search_params = request.session.get('search_params', {})

                back_url = (
                    reverse('recipe_list') + f"?{urlencode(search_params, doseq=True)}"
                    if search_params else reverse('recipe_list')
                )
                context['back_url'] = back_url
                request.session.pop('was_editing', None)

            else:
                context['back_url'] = (
                    request.META.get('HTTP_REFERER') or reverse('recipe_list')
                )
        else:
            context['back_url'] = reverse('index')

        return context


class RecipeEditView(UpdateView):
    """View for editing an existing recipe and its ingredients."""
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipe_generator/recipe_edit.html'

    def get_context_data(self, **kwargs):
        """Add ingredient formset to the template context."""
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = RecipeIngredientFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            context['formset'] = RecipeIngredientFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        """Save form and formset if valid, then redirect."""
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            self.request.session['was_editing'] = True
            return redirect(reverse(
                'recipe_detail',
                kwargs={'pk': self.object.pk}
            ))
        return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle invalid form submission."""
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class RecipeDeleteView(DeleteView):
    """View for confirming and deleting a recipe."""
    model = Recipe
    template_name = 'recipe_generator/recipe_delete.html'
    success_url = reverse_lazy('index')


class RecipeList(ListView):
    """List and filter recipes based on search query and ingredients."""
    model = Recipe
    paginate_by = 15
    template_name = "recipe_generator/recipe_list.html"
    context_object_name = 'recipes'

    def get(self, request, *args, **kwargs):
        """Track session origin and store query params."""
        request.session['came_from_search'] = True
        allowed_params = {
            k: request.GET.getlist(k) for k in ALLOWED_SEARCH_PARAMS
            if k in request.GET and any(request.GET.getlist(k))
        }
        request.session['search_params'] = allowed_params
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """Apply filters and search for name, ingredients, time, and exclusions."""
        query_ingredients = [
            int(i) for i in self.request.GET.getlist('query_ingredients')
            if i.isdigit()
        ]
        exclude_ingredients = [
            int(i) for i in self.request.GET.getlist('exclude_ingredients')
            if i.isdigit()
        ]
        query_name = self.request.GET.get('query_name', '')
        time_filter = self.request.GET.get('cooking_time')

        qs = Recipe.objects.search(
            query_name=query_name,
            query_ingredients=query_ingredients
        ).filter_recipes(
            time_filter=time_filter,
            exclude_ingredients=exclude_ingredients
        ).prefetch_related('ingredients').order_by('id')

        if query_ingredients:
            ingredient_lookup_query = {
                i.id: i.name for i in Ingredient.objects.filter(
                    id__in=query_ingredients
                )
            }

            for recipe in qs:
                recipe_ingredient_ids = set(
                    recipe.ingredients.values_list('id', flat=True)
                )
                matching_ids = recipe_ingredient_ids.intersection(
                    set(query_ingredients)
                )
                missing_ids = set(recipe_ingredient_ids) - set(query_ingredients)

                ingredient_lookup_recipe = {
                    i.id: i.name for i in Ingredient.objects.filter(
                        id__in=missing_ids
                    )
                }

                recipe.matching_ingredient_ids = list(matching_ids)
                recipe.missing_ingredient_ids = list(missing_ids)

                recipe.matching_ingredient_names = [
                    ingredient_lookup_query[i] for i in matching_ids
                ]
                recipe.missing_ingredient_names = [
                    ingredient_lookup_recipe[i] for i in missing_ids
                ]

        return qs

    def get_context_data(self, **kwargs):
        """Add filter- and search- related data to context."""
        context = super().get_context_data(**kwargs)

        context['current_cooking_time'] = self.request.GET.get(
            'cooking_time', ''
        )
        context['all_ingredients'] = Ingredient.objects.all()
        context['query_ingredients'] = self.request.GET.getlist(
            'query_ingredients', ''
        )
        context['query_name'] = self.request.GET.get('query_name', '')
        context['exclude_ingredients'] = self.request.GET.getlist(
            'exclude_ingredients'
        )

        return context


def index_view(request):
    """Render homepage and clear search tracking."""
    if 'came_from_search' in request.session:
        request.session.pop('came_from_search', None)
        request.session.pop('search_params', None)
    return render(request, 'recipe_generator/index.html')
