.PHONY: up down demo logs shell migrate migrate-docker makemigrations makemigrations-docker superuser seed

# ── Docker ────────────────────────────────────────────────────────────────────

up:
	docker compose up --build -d

down:
	docker compose down -v

logs:
	docker compose logs -f web

shell:
	docker compose exec web python manage.py shell

# ── Database ──────────────────────────────────────────────────────────────────

migrate:
	python manage.py migrate

migrate-docker:
	docker compose exec web python manage.py migrate

makemigrations:
	python manage.py makemigrations

makemigrations-docker:
	docker compose exec web python manage.py makemigrations

superuser:
	docker compose exec web python manage.py createsuperuser

# ── Seed ──────────────────────────────────────────────────────────────────────

seed:
	docker compose exec web python seed_demo_data.py

# ── Local dev (no Docker) ─────────────────────────────────────────────────────

run:
	python manage.py runserver

# ── Quick start ───────────────────────────────────────────────────────────────

demo:
	docker compose up --build -d
	sleep 5
	docker compose exec web python manage.py migrate
	docker compose exec web python seed_demo_data.py