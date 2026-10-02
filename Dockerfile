FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
RUN mkdir app && touch app/__init__.py && pip install ".[dev]" && rm -rf app

COPY . .
RUN pip install --no-deps -e .

RUN useradd --create-home --uid 1000 greenocr && mkdir -p data storage && chown -R greenocr /app
USER greenocr

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000"]
