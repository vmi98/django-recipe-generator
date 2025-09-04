# Recipe Generator App

A Django-based web application for managing and searching recipes based on recipe name and ingredients. Users can create, edit, delete, and store recipes, with support for both traditional HTML views and RESTful API endpoints using Django Rest Framework (DRF).

## Features

- CRUD for recipes and ingredients
- Search recipes by name 
- Search recipes by ingredients (for each recipe it shows what you have and what’s missing)
- Filter by:
  - Cooking time
  - Excluded ingredients
- Dual interface: Django templates and DRF API
- API endpoints are secured using Token Authentication (DRF), HTML routes are secured using Session Authentication.
- Access Control: read access - open to all users, create access - restricted to authenticated users. Recipes: update/delete - only the recipe creator or admin users. Ingredients: update/delete - restricted to admin users only.

## Tech Stack

- Python
- Django
- Django REST Framework
- PostgreSQL
- Django ORM
- unittest (testing)
- Docker
- Gunicorn (production server)
- uv (package management)
- flake8 (linting)
- coverage (test coverage)

## API
Access via recipe_generator/api/

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

Authentication: TokenAuthentication

Example Request for adding new recipe (cURL):
```
curl --location 'https://django-recipe-generator.onrender.com/recipe_generator/api/recipes/' \
--header 'Authorization: Token 123xyz' \
--header 'Content-Type: application/json' \
--data '{
    "ingredients": [
        {
            "ingredient": 6,
            "quantity": "90 g"
        },
        {
            "ingredient": 8,
            "quantity": "50 g"
        }
    ],
    "name": "Salad",
    "instructions": "Put ingredients together, mix",
    "cooking_time": 5
}
'
```
Example Response (JSON):
```
{
    "id": 53,
    "ingredients": [
        {
            "ingredient": {
                "id": 6,
                "name": "Cucumber"
            },
            "quantity": "90 g"
        },
        {
            "ingredient": {
                "id": 8,
                "name": "Tomato"
            },
            "quantity": "50 g"
        }
    ],
    "name": "Salad",
    "instructions": "Put ingredients together, mix",
    "cooking_time": 5
}
```

## Run with docker

Set the following variables in your .env file
```
SECRET_KEY=your-secret-key
DB_NAME=recipegenerator 
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=db # leave this for docker compose
DB_PORT=5432

DEBUG=False

DJANGO_SUPERUSER_USERNAME=your_user
DJANGO_SUPERUSER_EMAIL=your_user_email@example.com
DJANGO_SUPERUSER_PASSWORD=your_password

DJANGO_ALLOWED_HOSTS=example.com,www.example.com
```

```
git clone https://github.com/vmi98/django-recipe-generator.git
cd django-recipe-generator

docker compose build
docker compose up
```

## Running the tests
```
docker-compose up -d
docker-compose exec web uv run coverage run  manage.py test
docker-compose exec web uv run coverage report
```

## Linting
```
docker-compose up -d
docker-compose exec web uv run flake8 .
```

## Deployment Notes

Dockerized and deployed on [Render](https://django-recipe-generator-latest.onrender.com)