# Stage 1: Build virtual environment
FROM python:3.14-alpine AS builder

# Install system dependencies needed to build/fetch git dependencies
RUN apk add --no-cache git build-base

# Set up virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install build dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools poetry-core

# Set working directory
WORKDIR /app

# Copy project definition and files needed for installation
COPY pyproject.toml /app/
COPY airlink2mqtt /app/airlink2mqtt

# Install project and dependencies into the virtual environment
RUN pip install --no-cache-dir .

# Stage 2: Final minimal runtime image
FROM python:3.14-alpine

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Set entrypoint to run the tool
ENTRYPOINT ["airlink2mqtt"]
