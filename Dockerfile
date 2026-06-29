# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
# Licensed under the GNU Affero General Public License v3 or later.

# Multi-stage build that keeps the final image small.
FROM python:3.11-slim AS base

# Timezone (defaults to Asia/Shanghai for the maintainer; override at runtime).
ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        curl \
        tzdata \
        build-essential \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Install Python deps first (better layer caching).
COPY requirements.txt optional-requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt \
    && (pip install -r optional-requirements.txt || true)

# Copy the project.
COPY . .

# Default HF Spaces port. The wizard listens here.
ENV HOST=0.0.0.0 \
    PORT=7860 \
    HOSTED_ON=docker

EXPOSE 7860

# One-command startup.
CMD ["python", "zelretch.py"]
