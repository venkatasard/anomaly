.PHONY: up down test lint seed simulate
up:
	docker compose up --build
down:
	docker compose down
test:
	docker compose run --rm api pytest
lint:
	docker compose run --rm api ruff check app tests
	cd frontend && npm run lint
seed:
	docker compose exec api python -m app.scripts.seed
simulate:
	docker compose exec api python -m app.scripts.simulate --events 60000

