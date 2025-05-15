# Recipe Generator App

A Django-based web application for searching recipes baced on recipe name and ingredients. Offers both traditional HTML views and RESTful API endpoints.

## Features

- Search recipes by name 
- Search recipes by ingredients (for each recipe it shows what you have and what’s missing)
- Filter by:
  - Cooking time
  - Excluded ingredients
- Dual interface: Django templates and DRF API

## Tech Stack

- Python
- Django
- Django REST Framework
- SQLite (default database)
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
    GET     /recipe-form-data/      - Retrieve form-related data
                                    (provides available ingredients)
    POST    /api-token-auth/        - Log in, obtain authentication token
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
```
git clone https://github.com/vmi98/django-recipe-generator.git
cd django-recipe-generator

docker build -t django-recipe-generator .
docker run -p 8000:8000 django-recipe-generator
```

## Running the tests
```
uv run coverage run manage.py test
uv run coverage report
```

## Linting
```
uv run flake8 .
```

## Deployment Notes

Dockerized and deployed on Render