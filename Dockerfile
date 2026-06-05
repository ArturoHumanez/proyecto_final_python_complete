FROM python:3.12-slim AS builder

RUN pip install poetry==2.3.1 poetry-plugin-export

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry export -f requirements.txt --without dev -o requirements.txt

FROM python:3.12-slim AS runtime

WORKDIR /app

RUN useradd --create-home appuser

COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY .env.docker .env


RUN mkdir -p /app/data && chown appuser:appuser /app/data

USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]