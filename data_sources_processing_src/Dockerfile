FROM python:3.11.5-slim

LABEL maintainer="CPAoR dev team"
LABEL org.opencontainers.image.source="https://github.com/GCPAoR/cpaor-data-viz-dashboard"

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get -y install --no-install-recommends \
    cron \
    curl \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock /app/
COPY crontab /etc/cron.d/processing_cron
RUN chmod 0644 /etc/cron.d/processing_cron
COPY update_datasets.py /app/update_datasets.py
RUN chmod +x /app/update_datasets.py
COPY ./data_sources_processing/datasets_metadata.json /data/datasets_metadata.json

RUN crontab /etc/cron.d/processing_cron

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

RUN python -m nltk.downloader punkt
