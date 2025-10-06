"""
URL configuration for the Recipe Generator API.

Available endpoints:

    GET     /api/recipes/           - List all recipes
    POST    /api/recipes/           - Create a recipe
    GET     /api/recipes/<id>/      - Retrieve a recipe
    PUT     /api/recipes/<id>/      - Update a recipe
    DELETE  /api/recipes/<id>/      - Delete a recipe
    POST    /filter_search/         - Filter/search recipes

    GET     /api/ingredients/       - List all ingredients
    POST    /api/ingredients/       - Create an ingredients
    GET     /api/ingredients/<id>/  - Retrieve an ingredient
    PUT     /api/ingredients/<id>/  - Update an ingredient
    DELETE  /api/ingredients/<id>/  - Delete an ingredient

    POST    /api-token-auth/        - Obtain authentication token
    POST    /register/              - Register a new user
    GET     /docs/                  - Swagger UI
    GET     /schema/                - OpenAPI schema

    POST    /auth/login/            - Login
    POST    /auth/logout/           - Logout
    POST    /auth/registration/     - Register
    POST    /auth/jwt/refresh/      - Refresh token
    POST    /auth/jwt/verify/       - Verify token
"""
from django.urls import path
from django.urls import include
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from dj_rest_auth.registration.views import VerifyEmailView
from django_recipe_generator.recipe_generator.api import views


router = DefaultRouter()
router.register(r'recipes', views.RecipeViewSet, basename='recipe')
router.register(r'ingredients', views.IngredientViewSet, basename='ingredient')

urlpatterns = [
    path("", include([
        path("", views.RecipeViewSet.as_view({'get': 'api_root'}),
             name='api-root'),
        path("", include(router.urls)),

        path("api-token-auth/", obtain_auth_token, name='api-token-auth'),

        path("dj-rest-auth/", include("dj_rest_auth.urls")),
        path("dj-rest-auth/registration/", include("dj_rest_auth.registration.urls")),
        path("dj-rest-auth/social/google/", views.GoogleLogin.as_view(), name='google_login'),
        path("dj-rest-auth/account-confirm-email/", VerifyEmailView.as_view(),
             name='account_email_verification_sent'),
        path("schema/", SpectacularAPIView.as_view(), name='schema'),
        path("docs/", SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    ])),
]
