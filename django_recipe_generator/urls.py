"""
URL configuration for django_recipe_generator project.

This module defines the URL patterns for the project, including:
- The root URL serving a project description page.
- The recipe_generator app URLs.
- The Django admin interface.
"""
from django.contrib import admin
from allauth.account.decorators import secure_admin_login
from django.urls import path
from django.urls import include
from django.views.generic import TemplateView

# allauth admin
admin.autodiscover()
admin.site.login = secure_admin_login(admin.site.login)

urlpatterns = [
    path('', TemplateView.as_view(template_name="project_page.html")),
    path('recipe_generator/',
         include('django_recipe_generator.recipe_generator.urls')),
    path('admin/', admin.site.urls),
]
