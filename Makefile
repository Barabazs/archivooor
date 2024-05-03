help:
	@echo "lint - lint code"
	@echo "install-dev - install all dependencies for development"

install-dev:
	poetry install --with dev --all-extras

lint:
	@ERROR=0; \
	poetry run isort archivooor || ERROR=1; \
	poetry run black archivooor || ERROR=1; \
	poetry run pydocstyle archivooor || ERROR=1; \
	poetry run pylint archivooor || ERROR=1; \
	poetry run mypy archivooor || ERROR=1; \
	poetry run pre-commit run --all || ERROR=1; \
	exit $$ERROR
