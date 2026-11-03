# Aptare

Turns one structured profile into a tailored LaTeX resume for each job posting. Runs locally first, later as a hosted instance where users bring their own API keys.

## Prerequisites

Docker, [uv](https://docs.astral.sh/uv/), Node 22, Python 3.12.

## Run it

```
make dev
```

Then open <http://localhost:8080>. The first run builds three images and downloads the LaTeX packages the compile worker needs, so it takes a few minutes; later runs start in seconds. Your data lives in `./data`. Stop with `Ctrl+C`, and `make down` removes the containers.

`make smoke` checks a running stack end to end: it renders a resume, downloads the PDF, compares its hash, and confirms the compile worker has no internet access.

## Commands

| Command | What it does |
|---|---|
| `make install` | Install backend, compiler and frontend dependencies |
| `make dev` | Build and run api, compiler and frontend with Docker Compose (<http://localhost:8080>) |
| `make down` | Stop and remove the containers (`./data` is kept) |
| `make smoke` | End-to-end check of the running stack |
| `make test` | Backend and compiler pytest, frontend vitest |
| `make test-compile` | `pytest -m compile` (needs the compiler image) |
| `make lint` | ruff, mypy, eslint, tsc, prettier |
| `make fmt` | Auto-fix formatting |
| `make typegen` | Regenerate frontend API types from OpenAPI |
| `make e2e` | Playwright against docker compose with `LLM_PROVIDER=fake` |

`make dev` needs no `.env`: compose sets what the containers need. To run the API or the web page by hand instead (`uv run uvicorn ...`, `npm run dev`), copy `.env.example` to `.env` in the repo root and change `COMPILER_URL` to `http://localhost:8001`, the address of the worker when you run it with `docker run -p 8001:8001`. A `backend/.env`, if present, overrides the root one.
