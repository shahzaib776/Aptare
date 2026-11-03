# Aptare

Turns one structured profile into a tailored LaTeX resume for each job posting. Runs locally first, later as a hosted instance where users bring their own API keys.

## Prerequisites

Docker, [uv](https://docs.astral.sh/uv/), Node 22, Python 3.12.

## Commands

| Command | What it does |
|---|---|
| `make install` | Install backend, compiler and frontend dependencies |
| `make dev` | `docker compose up` (api, compiler, frontend) |
| `make test` | Backend and compiler pytest, frontend vitest |
| `make test-compile` | `pytest -m compile` (needs the compiler image) |
| `make lint` | ruff, mypy, eslint, tsc, prettier |
| `make fmt` | Auto-fix formatting |
| `make typegen` | Regenerate frontend API types from OpenAPI |
| `make e2e` | Playwright against docker compose with `LLM_PROVIDER=fake` |

Copy `.env.example` to `.env` in the repo root before running. A `backend/.env`, if present, overrides it.
