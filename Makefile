.DEFAULT_GOAL := help
UV ?= uv

.PHONY: help setup up down install ingest demo eval search test lint format check clean reset

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-9s\033[0m %s\n", $$1, $$2}'

setup: up install ingest ## One-shot: start OpenSearch, install deps, index data

up: ## Start OpenSearch (Docker) and wait until healthy
	docker compose up -d opensearch
	@printf "waiting for OpenSearch"
	@until curl -fs localhost:9200/_cluster/health >/dev/null 2>&1; do printf "."; sleep 2; done
	@echo " ready"

down: ## Stop containers
	docker compose down

install: ## Sync dependencies into uv-managed .venv (incl. dev tools)
	$(UV) sync --extra dev

ingest: ## Index the synthetic candidates
	$(UV) run zeil ingest

demo: ## Run the Part 1 + Part 2 demo
	$(UV) run zeil demo

eval: ## Run the eval harness (Part 3 metrics)
	$(UV) run zeil eval

search: ## Search, e.g. make search Q="truck driver near Parramatta" PROX=30
	$(UV) run zeil search "$(Q)" $(if $(PROX),--proximity-km $(PROX),)

test: ## Run the test suite
	$(UV) run pytest -q

lint: ## Lint with ruff
	$(UV) run ruff check .

format: ## Auto-format with ruff
	$(UV) run ruff format .

check: lint test ## Lint + run tests

clean: ## Remove python/test caches
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

reset: ## Stop containers and delete the index volume
	docker compose down -v
