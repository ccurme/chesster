coverage:
	poetry run python -m pytest --cov \
		--cov-config=.coveragerc \
		--cov-report xml \
		--cov-report term-missing:skip-covered

format:
	poetry run black .
	poetry run isort .

lint:
	poetry run mypy .
	poetry run black . --check
	poetry run isort . --check
	poetry run flake8 .

start:
	# Ctrl+C will kill both servers
	/bin/bash -c "trap 'kill %1; kill %2' SIGINT; \
	uvicorn chesster.app.app:app & \
	python chesster/langserve/langserver.py & \
	wait"

unit_tests:
	poetry run python -m pytest tests/unit_tests
