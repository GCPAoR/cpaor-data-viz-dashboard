FROM python:3.11.5-slim
COPY --from=ghcr.io/astral-sh/uv:0.6.8 /uv /uvx /bin/

LABEL maintainer="CPAoR dev team"
LABEL org.opencontainers.image.source="https://github.com/GCPAoR/cpaor-data-viz-dashboard"

ENV PYTHONUNBUFFERED=1

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"

WORKDIR /app

RUN apt-get update && apt-get -y install --no-install-recommends \
    cron \
    curl \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock /app/
COPY crontab /etc/cron.d/processing_cron
RUN chmod 0644 /etc/cron.d/processing_cron
COPY update_datasets.py /app/update_datasets.py
RUN chmod +x /app/update_datasets.py
COPY ./data_sources_processing/datasets_metadata.json /data/datasets_metadata.json

RUN crontab /etc/cron.d/processing_cron

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    apt-get update -y \
    && apt-get install -y --no-install-recommends \
        # Build required packages
        gcc libc-dev gdal-bin libproj-dev \
        # Helper packages
        procps \
        wait-for-it \
    # FIXME: Add condition to skip dev dependencies
    && uv sync --frozen --no-install-project --all-groups \
    # Clean-up
    && apt-get remove -y gcc libc-dev libproj-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/

RUN [ "python3", "-c", "import nltk; nltk.download('punkt_tab', download_dir='/usr/local/nltk_data')" ]
