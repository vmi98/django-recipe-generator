"""
Forms for managing Recipe and RecipeIngredient data.

Includes model forms for recipes and ingredients, with validation and
formset logic for handling inline recipe ingredients.
"""
from django import forms
from django.core.validators import MaxLengthValidator
from django.core.exceptions import ValidationError
from .models import Recipe, RecipeIngredient


class RecipeIngredientForm(forms.ModelForm):
    """Form for creating or editing a single RecipeIngredient."""
    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'quantity')
        widgets = {
            'ingredient': forms.Select(),
            'quantity': forms.TextInput(),
        }


class RecipeForm(forms.ModelForm):
    """Form for creating or editing a Recipe instance."""
    class Meta:
        model = Recipe
        exclude = ['ingredients']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'instructions': forms.Textarea(
                attrs={'rows': 4, 'maxlength': 2000, 'class': 'textarea'}
            ),
            'cooking_time': forms.NumberInput(
                attrs={'min': 1, 'class': 'input'}
            )
        }

    cooking_time = forms.IntegerField(
        help_text="in minutes (e.g., 30 minutes)"
    )

    def __init__(self, *args, **kwargs):
        """Attach a max length validator to the instructions field."""
        super().__init__(*args, **kwargs)
        self.fields['instructions'].validators.append(MaxLengthValidator(2000))

    def clean_name(self):
        """Validate that the recipe name has a minimum length of 3 characters."""
        name = self.cleaned_data['name']
        if len(name) < 3:
            raise forms.ValidationError("Name too short!")
        return name


class BaseRecipeIngredientFormSet(forms.BaseInlineFormSet):
    """Formset for managing multiple RecipeIngredient forms."""
    def clean(self):
        """Validate ingredient uniqueness, count, and quantity presence."""
        super().clean()

        total_ingredients = 0
        ingredients = []
        for form in self.forms:
            ingredient = form.cleaned_data.get("ingredient")
            quantity = form.cleaned_data.get("quantity")

            if form.cleaned_data.get('DELETE', False):
                continue
            if not ingredient or not quantity:
                continue
            if ingredient in ingredients:
                raise forms.ValidationError(
                    "You can't add the same ingredient again"
                )
            ingredients.append(form.cleaned_data.get('ingredient'))
            total_ingredients += 1

        if total_ingredients < 1:
            raise forms.ValidationError(
                "You must have at least one ingredient (with quantity field filled)."
            )

        if total_ingredients > 20:
            raise ValidationError("Ingredients per recipe limit exceeded.")


# Create a formset factory
RecipeIngredientFormSet = forms.inlineformset_factory(
    Recipe,
    RecipeIngredient,
    form=RecipeIngredientForm,
    formset=BaseRecipeIngredientFormSet,
    extra=5,  # Number of empty forms to display
    can_delete=True,
)
