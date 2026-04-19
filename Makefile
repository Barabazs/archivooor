help:
	@echo "lint - lint code"
	@echo "install-dev - install all dependencies for development"
	@echo "test - run tests"

install-dev:
	uv sync --all-extras --dev

test:
	uv run pytest

lint:
	@ERROR=0; \
	uv run ruff check --fix || ERROR=1; \
	uv run mypy archivooor || ERROR=1; \
	exit $$ERROR
