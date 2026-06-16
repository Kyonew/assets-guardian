# Stage 1 : Build
FROM python:3.13-slim-trixie AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.19 /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies first (Docker cache)
COPY pyproject.toml README.md uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Then the source code
COPY src/ src/
RUN uv sync --frozen --no-dev

# Stage 2 : Runtime
FROM python:3.13-slim-trixie AS runtime

# OCI image metadata, VERSION and BUILD_DATE are injected at build time (--build-arg) with fallbacks for local builds
ARG VERSION=dev
ARG BUILD_DATE=unknown
LABEL org.opencontainers.image.title="assets-guardian" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.source="https://github.com/apizee/assets-guardian"

RUN groupadd --gid 1000 guardian && \
    useradd --uid 1000 --gid guardian --create-home guardian

WORKDIR /app

# Copy only the built venv + the code
COPY --from=builder --chown=guardian:guardian /app /app

# Output directories + build metadata (readable at runtime in /app/build-info.txt)
RUN mkdir -p /app/outputs /app/logs /app/.assets-guardian_cache /app/config && \
    chown -R guardian:guardian /app/outputs /app/logs /app/.assets-guardian_cache /app/config && \
    printf 'Version: %s\nDate: %s\n' "${VERSION}" "${BUILD_DATE}" > /app/build-info.txt && \
    chown guardian:guardian /app/build-info.txt

USER guardian

ENTRYPOINT ["/app/.venv/bin/assets-guardian"]
CMD ["--help"]
