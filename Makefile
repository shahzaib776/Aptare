.PHONY: install dev test test-compile lint fmt typegen e2e

install:
	cd backend && uv sync
	cd compiler && uv sync
	cd frontend && npm ci

dev:
	docker compose up

test:
	cd backend && uv run pytest -m "not compile and not live"
	cd compiler && uv run pytest -m "not compile"
	cd frontend && npm test

# The backend has no compile tests yet and pytest exits 5 when nothing is collected. The compiler
# ones run in the image with no network, which proves the offline package cache is complete.
test-compile:
	cd backend && uv run pytest -m compile; code=$$?; [ $$code -eq 5 ] || exit $$code
	docker build -f compiler/Dockerfile --target test -t aptare-compiler-test .
	docker run --rm --network none aptare-compiler-test

lint:
	cd backend && uv run ruff check && uv run ruff format --check && uv run mypy
	cd compiler && uv run ruff check && uv run ruff format --check && uv run mypy
	cd frontend && npm run lint && npm run typecheck && npm run format:check

fmt:
	cd backend && uv run ruff check --fix && uv run ruff format
	cd compiler && uv run ruff check --fix && uv run ruff format
	cd frontend && npm run format

# The generated file is committed, so lint and typecheck never need Python. Settings use an
# in-memory database so dumping the schema creates no data/ folder.
typegen:
	cd backend && uv run python -c "import json; from app.config import Settings; from app.main import create_app; print(json.dumps(create_app(Settings(db_url='sqlite://')).openapi(), indent=2))" > ../frontend/openapi.json
	cd frontend && npm run typegen

e2e:
	@echo "e2e needs docker-compose (step 14) and Playwright (Phase 2)" >&2; exit 1
