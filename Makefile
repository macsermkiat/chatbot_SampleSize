# Project root Makefile
# Always use the backend .venv to avoid system Python conflicts

BACKEND_DIR := backend
FRONTEND_DIR := frontend
# Paths relative to BACKEND_DIR (used after cd into it)
VENV_BIN := .venv/bin
PYTHON := $(VENV_BIN)/python
UVICORN := $(VENV_BIN)/uvicorn
PYTEST := $(VENV_BIN)/pytest

.PHONY: install dev backend frontend test lint clean

## First-time setup: create venv and install all deps
install:
	cd $(BACKEND_DIR) && uv venv .venv && uv pip install -e ".[dev]"
	cd $(FRONTEND_DIR) && npm install

## Start both backend and frontend (use with make -j2 dev)
dev: backend frontend

## Start backend (FastAPI on port 8000)
backend:
	cd $(BACKEND_DIR) && $(UVICORN) app.main:app --reload --port 8000 --timeout-keep-alive 300

## Start frontend (Next.js on port 3000)
frontend:
	cd $(FRONTEND_DIR) && npm run dev

## Run backend tests
test:
	cd $(BACKEND_DIR) && $(PYTEST)

## Run frontend lint
lint:
	cd $(FRONTEND_DIR) && npm run lint

## Verify venv is healthy (quick sanity check)
check-env:
	@cd $(BACKEND_DIR) && $(PYTHON) -c "import langchain_core; import uvicorn; import fastapi; print('Environment OK')"

## Clean generated files
clean:
	find $(BACKEND_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(BACKEND_DIR)/.pytest_cache
	rm -rf $(FRONTEND_DIR)/.next
