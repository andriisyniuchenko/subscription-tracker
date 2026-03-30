.PHONY: run migrate makemigrations superuser up down

run:
	python manage.py runserver

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

superuser:
	python manage.py createsuperuser

up:
	docker compose up --build -d

down:
	docker compose down -v