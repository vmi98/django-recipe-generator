from django.shortcuts import render, redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Recipe, Ingredient
from .serializers import RecipeSerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import DetailView, DeleteView, ListView
from django.urls import reverse_lazy
from .forms import RecipeForm, RecipeIngredientFormSet


class RecipeCreateView(CreateView):
    model = Recipe
    form_class = RecipeForm 
    template_name = 'recipe_generator/create.html'
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        formset = RecipeIngredientFormSet()
        return render(request, self.template_name, {'form': form, 'formset': formset})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        formset = RecipeIngredientFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            recipe = form.save()
            formset.instance = recipe
            formset.save()
            return redirect(reverse('recipe_detail', kwargs={'pk': recipe.pk}))

        return render(request, self.template_name, {'form': form, 'formset': formset})

class RecipeDetailView(DetailView):
    model = Recipe  
    template_name = 'recipe_generator/recipe_detail.html'  
    context_object_name = 'recipe'


class RecipeEditView(UpdateView):
    model = Recipe  
    form_class = RecipeForm
    template_name = 'recipe_generator/recipe_edit.html'  

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = RecipeIngredientFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = RecipeIngredientFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            return redirect(reverse('recipe_detail', kwargs={'pk': self.object.pk}))
        else:
            return self.render_to_response(self.get_context_data(form=form))


class RecipeDeleteView(DeleteView):
    model = Recipe
    template_name = 'recipe_generator/recipe_delete.html'
    success_url = reverse_lazy('index')


class RecipeList(ListView): # search filters
    model = Recipe 
    paginate_by = 15  
    template_name = "recipe_generator/recipe_list.html"
    context_object_name = 'recipes'
    
    def get_queryset(self):
        query_ingredients = [int(i) for i in self.request.GET.getlist('query_ingredients') if i.isdigit()]
        exclude_ingredients = [int(i) for i in self.request.GET.getlist('exclude_ingredients') if i.isdigit()]
        query_name = self.request.GET.get('query_name', '')
        time_filter = self.request.GET.get('cooking_time')

        qs = Recipe.objects.search(query_name=query_name,query_ingredients=query_ingredients).filter_recipes(time_filter=time_filter,
            exclude_ingredients=exclude_ingredients).prefetch_related('ingredients')

        ingredient_lookup_query = {i.id: i.name for i in Ingredient.objects.filter(id__in=query_ingredients)}

        for recipe in qs:
            recipe_ingredient_ids = set(recipe.ingredients.values_list('id', flat=True))
            matching_ids = recipe_ingredient_ids.intersection(set(query_ingredients))
            missing_ids = set(recipe_ingredient_ids) - set(query_ingredients)

            ingredient_lookup_recipe = {i.id: i.name for i in Ingredient.objects.filter(id__in=missing_ids)}

            recipe.matching_ingredient_ids = list(matching_ids)
            recipe.missing_ingredient_ids = list(missing_ids)

            recipe.matching_ingredient_names = [ingredient_lookup_query[i] for i in matching_ids]
            recipe.missing_ingredient_names = [ingredient_lookup_recipe[i] for i in missing_ids]

        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_cooking_time'] = self.request.GET.get('cooking_time', '')
        context['all_ingredients'] = Ingredient.objects.all()
        context['query_ingredients'] = self.request.GET.getlist('query_ingredients', '')
        context['query_name'] = self.request.GET.get('query_name', '')
        context['exclude_ingredients'] = self.request.GET.getlist('exclude_ingredients')

        return context



# API logic    
class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer


 
