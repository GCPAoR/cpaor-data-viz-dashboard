FROM python:3.11.5-slim
COPY --from=ghcr.io/astral-sh/uv:0.6.8 /uv /uvx /bin/

LABEL maintainer="CPAoR dev team"
LABEL org.opencontainers.image.source="https://github.com/GCPAoR/cpaor-data-viz-dashboard"

ENV PYTHONUNBUFFERED=1

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"

WORKDIR /app

RUN apt-get update \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock /app/

# Upgrade pip and install python packages for app
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
