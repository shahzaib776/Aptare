# Build from the repository root so the test stage can reach the golden .tex files:
#   docker build -f compiler/Dockerfile --target test -t aptare-compiler-test .
#   docker build -f compiler/Dockerfile -t aptare-compiler .

FROM python:3.12-slim AS tectonic
ARG TARGETARCH
ARG TECTONIC_VERSION=0.17.0
ARG TECTONIC_SHA256_ARM64=b10954a95404f3ab2328d2fa59a5ebab8e657f893fab096f98be8db7c0c979b8
ARG TECTONIC_SHA256_AMD64=8533d07f9ccbd7a65824b9e0459041bca34af1eb33daba48f59215593753a3b7
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN set -eux; \
    case "$TARGETARCH" in \
      arm64) triple=aarch64-unknown-linux-musl; sha="$TECTONIC_SHA256_ARM64" ;; \
      amd64) triple=x86_64-unknown-linux-musl; sha="$TECTONIC_SHA256_AMD64" ;; \
      *) echo "unsupported architecture: $TARGETARCH" >&2; exit 1 ;; \
    esac; \
    curl -fsSL -o /tmp/tectonic.tar.gz \
      "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40${TECTONIC_VERSION}/tectonic-${TECTONIC_VERSION}-${triple}.tar.gz"; \
    echo "${sha}  /tmp/tectonic.tar.gz" | sha256sum -c -; \
    tar -xzf /tmp/tectonic.tar.gz -C /usr/local/bin tectonic

FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.11.23 /uv /usr/local/bin/uv
COPY --from=tectonic /usr/local/bin/tectonic /usr/local/bin/tectonic
RUN useradd --create-home --uid 10001 compiler
WORKDIR /app
ENV UV_LINK_MODE=copy PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"
COPY compiler/pyproject.toml compiler/uv.lock ./
RUN uv sync --frozen --no-dev
COPY compiler/worker ./worker
USER compiler
# The only step that needs the internet: fill Tectonic's package cache. Every later compile
# runs with --only-cached, so the container needs no network at all (rule 12).
COPY --chown=compiler compiler/warmup.tex /tmp/warmup/warmup.tex
RUN tectonic --outdir /tmp/warmup /tmp/warmup/warmup.tex && rm -rf /tmp/warmup

FROM base AS test
USER root
RUN uv sync --frozen
COPY compiler/tests ./tests
COPY backend/tests/golden /golden
ENV GOLDEN_DIR=/golden
USER compiler
CMD ["pytest", "-m", "compile", "-p", "no:cacheprovider"]

FROM base AS runtime
EXPOSE 8001
# ulimit -f caps the size of any file a compile can write (a runaway \write loop).
CMD ["sh", "-c", "ulimit -f 204800 && exec uvicorn worker.main:create_app --factory --host 0.0.0.0 --port 8001"]
