FROM python:3.11.5-slim

LABEL maintainer="CPAoR dev team"

ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock /app/

# Upgrade pip and install python packages for app
RUN pip install --upgrade --no-cache-dir pip poetry \
    && poetry --version \
    && poetry config installer.max-workers 4 \
    # Configure to use system instead of virtualenvs
    && poetry config virtualenvs.create false \
    && poetry install --no-root \
    # Remove installer
    && pip uninstall -y poetry virtualenv-clone virtualenv

COPY . /app/
