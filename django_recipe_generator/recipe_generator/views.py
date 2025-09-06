"""Traditional Djangoapp views.

Views for recipe creation, editing, deletion,
listing, and detail display.

Handles form processing, session tracking, and filtering logic.
"""

from django.shortcuts import render, redirect
from urllib.parse import urlencode

from django_recipe_generator.services.ingredients import annotate_recipes
from django_recipe_generator.services.gemini_client import get_unexpected_twist
from django.db.models import Prefetch
from django.urls import reverse, reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

from .forms import RecipeForm, RecipeIngredientFormSet, IngredientForm
from .models import Ingredient, Recipe, RecipeIngredient


ALLOWED_SEARCH_PARAMS = [
    'q',
    'query_ingredients',
    'time_filter',
    'exclude_ingredients',
    'query_name'
]


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only admins can access the view."""

    def test_func(self):
        return self.request.user.is_staff


class OwnerOrAdminRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only owners or admins can access the view."""

    def test_func(self):
        obj = self.get_object()
        return obj.owner == self.request.user or self.request.user.is_staff


class RecipeCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new recipe with inline ingredients."""

    model = Recipe
    form_class = RecipeForm
    template_name = 'recipe_generator/recipe_create.html'

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
            recipe = form.save(commit=False)
            recipe.owner = request.user
            recipe.save()
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
        """Inject back URL logic (depend on the prev page) for navigation context."""
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


class RecipeEditView(LoginRequiredMixin, OwnerOrAdminRequiredMixin, UpdateView):
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
        if formset.is_valid() and form.is_valid():
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


class RecipeDeleteView(LoginRequiredMixin, OwnerOrAdminRequiredMixin, DeleteView):
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

        ingredient_qs = Ingredient.objects.only('id', 'name')

        qs = Recipe.objects.search(
            query_name=query_name,
            query_ingredients=query_ingredients
        ).filter_recipes(
            time_filter=time_filter,
            exclude_ingredients=exclude_ingredients
        ).prefetch_related(
            Prefetch("ingredients", queryset=ingredient_qs))

        if query_ingredients:
            qs = annotate_recipes(qs, query_ingredients)

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


class IngredientCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new ingredient."""

    model = Ingredient
    form_class = IngredientForm
    template_name = 'recipe_generator/ingredient_create.html'

    def get(self, request, *args, **kwargs):
        """Display empty form and formset for ingredient creation."""
        form = self.form_class()
        return render(
            request,
            self.template_name,
            {'form': form}
        )

    def post(self, request, *args, **kwargs):
        """Handle form submission and create ingredient."""
        form = self.form_class(request.POST)

        if form.is_valid():
            ingredient = form.save()
            return redirect(reverse('ingredient_detail',
                                    kwargs={'pk': ingredient.pk}))

        return render(
            request,
            self.template_name,
            {'form': form}
        )


class IngredientDetailView(DetailView):
    """Display details of ingredient."""

    model = Ingredient
    template_name = 'recipe_generator/ingredient_detail.html'
    context_object_name = 'ingredient'


class IngredientEditView(AdminRequiredMixin, LoginRequiredMixin, UpdateView):
    """View for editing an existing ingredient."""

    model = Ingredient
    form_class = IngredientForm
    template_name = 'recipe_generator/ingredient_edit.html'

    def form_valid(self, form):
        """Save form if valid, then redirect."""
        if form.is_valid():
            self.object = form.save()
            return redirect(reverse(
                'ingredient_detail',
                kwargs={'pk': self.object.pk}
            ))
        return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle invalid form submission."""
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class IngredientDeleteView(AdminRequiredMixin, LoginRequiredMixin, DeleteView):
    """View for confirming and deleting a ingredient."""

    model = Ingredient
    template_name = 'recipe_generator/ingredient_delete.html'
    success_url = reverse_lazy('index')


class IngredientListView(ListView):
    """List of all ingredients."""

    model = Ingredient
    paginate_by = 15
    template_name = "recipe_generator/ingredient_list.html"
    context_object_name = 'ingredients'


def index_view(request):
    """Render homepage and clear search tracking."""
    if 'came_from_search' in request.session:
        request.session.pop('came_from_search', None)
        request.session.pop('search_params', None)
    return render(request, 'recipe_generator/index.html')


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Account created for {user.username}!")
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})
