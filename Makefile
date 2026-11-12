.PHONY: install lint test fmt precommit-install pyodide

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

pyodide:
	python3 -I scripts/fetch-pyodide.py
