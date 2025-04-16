from django import forms
from django.core.validators import MaxLengthValidator
from .models import Recipe, RecipeIngredient

class RecipeIngredientForm(forms.ModelForm):
    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'quantity')
        widgets = {
            'ingredient': forms.Select(attrs={'class': 'form-control'}), #class is bootstarp, delete if not used
            'quantity': forms.TextInput(attrs={'class': 'form-control'}),
        }



class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        exclude = ['ingredients']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'instructions': forms.Textarea(attrs={'rows': 4, 'maxlength': 2000}),
            'cooking_time': forms.NumberInput(attrs={'min': 1})
        }

    cooking_time = forms.IntegerField(help_text="in minutes (e.g., 30 minutes)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['instructions'].validators.append(MaxLengthValidator(2000))

    def clean_name(self):  
        name = self.cleaned_data['name']
        if len(name) < 3:
            raise forms.ValidationError("Name too short!")
        return name
    

# Create a formset factory
RecipeIngredientFormSet = forms.inlineformset_factory(
    Recipe,
    RecipeIngredient,
    form=RecipeIngredientForm,
    extra=5,  # Number of empty forms to display
    can_delete=False 
)