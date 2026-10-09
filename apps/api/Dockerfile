FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install --upgrade pip && pip install .

COPY alembic.ini ./
COPY alembic ./alembic

CMD ["sh", "-c", "alembic upgrade head && uvicorn job_hunt_api.main:app --host 0.0.0.0 --port 8000"]
