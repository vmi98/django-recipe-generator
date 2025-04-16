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
from django.views.generic.edit import CreateView
from .forms import RecipeForm, RecipeIngredientFormSet


class RecipeCreateView(CreateView):
    model = Recipe
    form_class = RecipeForm 
    template_name = "recipe_generator/create.html"
    
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
            return redirect('index')  # or any other page

        return render(request, self.template_name, {'form': form, 'formset': formset})


# API logic    
class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer


 
