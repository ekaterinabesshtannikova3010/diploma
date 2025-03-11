FROM python:3.12

RUN curl -sSL https://install.python-poetry.org | python -
WORKDIR /app

ENV PATH="/root/.local/bin:${PATH}"
ENV PYTHONPATH="/app"

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root