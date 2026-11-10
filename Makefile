.PHONY: install test lint check build

install:
	python -m pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check .
	ruff format --check .
	mypy

check: lint test

build:
	rm -rf dist && python -m build
