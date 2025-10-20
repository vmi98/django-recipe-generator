# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV PYTHONDONTWRITEBYTECODE=1
# Logs appear in real-time in Docker 
ENV PYTHONUNBUFFERED=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y postgresql-client && \
    rm -rf /var/lib/apt/lists/* 

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    #uv sync --frozen --no-install-project 
    uv sync --frozen --no-install-project --no-dev

# Add the rest of the project source code and install it
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    #uv sync --frozen
    uv sync --frozen --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Run the Django by default
#  0.0.0.0` to allow access from outside the container
#CMD ["./entrypoint.sh"]
#CMD ["uv", "run", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["gunicorn", "django_recipe_generator.wsgi:application", "--bind", "0.0.0.0:8000"]
