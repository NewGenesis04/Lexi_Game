.PHONY: dev backend frontend install test

# ---- dev ----

dev:
	$(MAKE) -j2 backend frontend

backend:
	uv run --directory packages/backend-api uvicorn backend_api.main:app --reload --port 8000

frontend:
	pnpm --dir frontend dev

# ---- setup / checks ----

install:
	uv sync --all-groups
	pnpm --dir frontend install

test:
	uv run --directory packages/game-engine pytest
	uv run --directory packages/backend-api pytest