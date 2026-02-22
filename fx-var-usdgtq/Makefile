.PHONY: install lint test run

install:
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt

lint:
	ruff check .
	black --check .

test:
	pytest -q

run:
	python -m src.pipeline
