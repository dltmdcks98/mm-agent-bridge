PYTHON ?= python
UV ?= uv
VENV ?= .venv
ACTIVATE = . $(VENV)/bin/activate

.PHONY: setup up down migrate run worker worker-once test lint

setup:
	$(UV) venv --python $(PYTHON) --clear $(VENV)
	$(UV) pip install --python $(VENV)/bin/python -e .[dev]

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down

migrate:
	psql postgresql://mm_bridge:mm_bridge@localhost:5432/mm_bridge -f sql/001_init.sql
	psql postgresql://mm_bridge:mm_bridge@localhost:5432/mm_bridge -f sql/002_add_response_url.sql

run:
	$(ACTIVATE) && uvicorn mm_agent_bridge.main:app --app-dir app/src --reload

worker:
	$(ACTIVATE) && python -m mm_agent_bridge.worker --poll-interval 1.0

worker-once:
	$(ACTIVATE) && python -m mm_agent_bridge.worker --once

test:
	$(ACTIVATE) && pytest

lint:
	$(ACTIVATE) && ruff check .
