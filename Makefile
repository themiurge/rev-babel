.PHONY: install lint test fmt

install:
	uv sync

lint:
	uv run ruff check .

fmt:
	uv run ruff format .

test:
	uv run pytest
