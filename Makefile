.PHONY: run migrate migrate-docker makemigrations superuser seed up down demo

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


seed:
	docker compose exec web python seed_demo_data.py

up:
	docker compose up --build -d

down:
	docker compose down -v

demo:
	make up
	sleep 5
	docker compose exec web python manage.py migrate
	make seed