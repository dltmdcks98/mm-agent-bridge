PYTHON ?= python3
VENV ?= .venv
ACTIVATE = . $(VENV)/bin/activate

.PHONY: setup up down migrate run test lint

setup:
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE) && pip install -e .[dev]

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down

migrate:
	psql postgresql://mm_bridge:mm_bridge@localhost:5432/mm_bridge -f sql/001_init.sql

run:
	$(ACTIVATE) && uvicorn mm_agent_bridge.main:app --app-dir app/src --reload

test:
	$(ACTIVATE) && pytest

lint:
	$(ACTIVATE) && ruff check .
