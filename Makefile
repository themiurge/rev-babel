.PHONY: install lint test fmt precommit-install

install:
	uv sync
	uv run pre-commit install

precommit-install:
	uv run pre-commit install

lint:
	uv run ruff check .

fmt:
	uv run ruff format .

test:
	uv run pytest
