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
- API endpoints are secured using JWT Authentication (DRF), HTML routes are secured using Session Authentication.
- Google OAuth 2.0 is implemented
- Access Control: read access - open to all users, create access - restricted to authenticated users. Recipes: update/delete - only the recipe creator or admin users. Ingredients: update/delete - restricted to admin users only.
- Gemini API integration: to each recipe gemini recommends special ingredient to elevate the dish and explain reason behaind it and how to use it (generates after saving new recipe or editing name or ingredients of existing one)

## Tech Stack

- Python
- Django
- Django REST Framework
- PostgreSQL
- Django ORM
- Allauth + dj-rest-auth + simple JWT
- unittest (testing)
- Docker
- Gunicorn (production server)
- uv (package management)
- flake8 (linting)
- coverage (test coverage)

## API
Access via recipe_generator/api/

Available endpoints via recipe_generator/api/schema or recipe_generator/api/docs/ 

Authentication: JWT Authentication

Example Request for adding new recipe (cURL):
```
curl --location 'https://django-recipe-generator.onrender.com/recipe_generator/api/recipes/' \
--header 'Authorization: Token 123xyz' \
--header 'Content-Type: application/json' \
--data '{
    "ingredients": [
        {
            "ingredient": 1,
            "quantity": "500 g"
        },
        {
            "ingredient": 2,
            "quantity": "200 g"
        },
        {
            "ingredient": 3,
            "quantity": "300 ml"
        },
        {
            "ingredient": 4,
            "quantity": "3 cloves"
        },
        {
            "ingredient": 5,
            "quantity": "1 tbsp"
        }
    ],
    "name": "Chicken Tikka Masalaa",
    "instructions": "Marinate chicken. Grill chicken. Prepare sauce. Combine and simmer",
    "cooking_time": 40
}
'
```
Example Response (JSON):
```
{
    "id": 1,
    "ingredients": [
        {
            "ingredient": {
                "id": 1,
                "name": "chicken breast"
            },
            "quantity": "500g"
        },
        {
            "ingredient": {
                "id": 2,
                "name": "yogurt"
            },
            "quantity": "200g"
        },
        {
            "ingredient": {
                "id": 3,
                "name": "tomato sauce"
            },
            "quantity": "300ml"
        },
        {
            "ingredient": {
                "id": 4,
                "name": "garlic"
            },
            "quantity": "3 cloves"
        },
        {
            "ingredient": {
                "id": 5,
                "name": "ginger"
            },
            "quantity": "1 tbsp"
        }
    ],
    "name": "Chicken Tikka Masalaa",
    "instructions": "Marinate chicken. Grill chicken. Prepare sauce. Combine and simmer",
    "cooking_time": 40,
    "elevating_twist": {
        "reason": "It adds a subtle earthy depth, a hint of bitterness to balance the richness, and a dark, complex umami note that complements the tomato and spice base without making the dish taste like chocolate. It deepens the overall complexity.",
        "how_to_use": "Whisk 1-2 teaspoons of unsweetened cocoa powder into the simmering tomato sauce base. Allow it to dissolve completely and meld with the other flavors for 5-10 minutes before adding the chicken.",
        "twist_ingredient": "Unsweetened Cocoa Powder"
    },
}
```

## Run with docker

Set the following variables in your .env file
```
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-secret-key
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

# for google auth
CLIENT_ID=client_id
CLIENT_SECRET=secret
CALLBACK_URL=url
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