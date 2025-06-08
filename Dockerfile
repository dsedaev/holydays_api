FROM python:3.9-slim-bookworm

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY pyproject.toml /app/

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-root

COPY . /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]