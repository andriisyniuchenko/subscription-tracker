.PHONY: run migrate migrate-docker makemigrations superuser up down

run:
	python manage.py runserver

migrate:
	python manage.py migrate

migrate-docker:
	docker compose exec web python manage.py migrate

makemigrations:
	python manage.py makemigrations

superuser:
	docker compose exec web python manage.py createsuperuser

up:
	docker compose up --build -d

down:
	docker compose down -v