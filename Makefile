# Build configuration
# -------------------

APP_NAME := `sed -n 's/^ *name.*=.*"\([^"]*\)".*/\1/p' pyproject.toml`
APP_VERSION := `sed -n 's/^ *version.*=.*"\([^"]*\)".*/\1/p' pyproject.toml`
GIT_REVISION = `git rev-parse HEAD`

# Introspection targets
# ---------------------

.PHONY: help
help: header targets

.PHONY: header
header:
	@echo "\033[34mEnvironment\033[0m"
	@echo "\033[34m---------------------------------------------------------------\033[0m"
	@printf "\033[33m%-23s\033[0m" "APP_NAME"
	@printf "\033[35m%s\033[0m" $(APP_NAME)
	@echo ""
	@printf "\033[33m%-23s\033[0m" "APP_VERSION"
	@printf "\033[35m%s\033[0m" $(APP_VERSION)
	@echo ""
	@printf "\033[33m%-23s\033[0m" "GIT_REVISION"
	@printf "\033[35m%s\033[0m" $(GIT_REVISION)
	@echo "\n"

.PHONY: targets
targets:
	@echo "\033[34mDevelopment Targets\033[0m"
	@echo "\033[34m---------------------------------------------------------------\033[0m"
	@perl -nle'print $& if m{^[a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

# Development targets
# -------------

.PHONY: install
install: ## Install dependencies
	poetry install

.PHONY: run
run: start

.PHONY: start
start: ## Starts the server
	poetry run python pre_start/up_postgresql.py
	poetry run python main.py

.PHONY: migrate
migrate: ## Run the migrations
	poetry run alembic upgrade head


.PHONY: deploy
deploy: ## Deploy
	poetry run alembic upgrade head
	poetry run python src/main.py

.PHONY: run
run: ## Run
	poetry run python src/main.py


.PHONY: rollback
rollback: ## Rollback migrations one level
	$(eval include .env)
	$(eval export $(sh sed 's/=.*//' .env))

	poetry run alembic downgrade -1

.PHONY: reset-database
reset-database: ## Rollback all migrations
	poetry run alembic downgrade base

.PHONY: migrations 
migrations: ## Generate a new migration
	poetry run python makemigrate.py

.PHONY: celery-worker
celery-worker: ## Start celery worker
	poetry run celery -A worker worker -l info

# Check, lint and format targets
# ------------------------------

.PHONY: check
check: check-format lint

.PHONY: check-format
check-format: ## Dry-run code formatter
	poetry run black ./ --check
	poetry run isort ./ --profile black --check

.PHONY: lint
lint: ## Run linter
	poetry run pylint ./api ./app ./core
 
.PHONY: format
format: ## Run code formatter
	poetry run black ./
	poetry run isort ./ --profile black

.PHONY: check-lockfile
check-lockfile: ## Compares lock file with pyproject.toml
	poetry lock --check

.PHONY: test
test: ## Run the test suite
	poetry run pytest -k "not test_spam_logins" -vv -s --cache-clear ./