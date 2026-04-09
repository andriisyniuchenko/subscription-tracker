# Subscription Tracker

[![CI](https://github.com/andriisyniuchenko/subscription-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/andriisyniuchenko/subscription-tracker/actions/workflows/ci.yml)

A Django web application for tracking personal subscriptions and recurring expenses. Supports multiple users, custom categories, and a 12-month cost forecast that accounts for subscription end dates.

---

## Features

- **Authentication** — registration, login, logout with session management
- **Subscription CRUD** — create, view, edit, and delete subscriptions
- **Custom categories** — each user creates their own categories; subscriptions are grouped by category on the dashboard with a per-category monthly total
- **Search & filter** — filter subscriptions by name, category, and status (active/inactive)
- **Sortable columns** — click any column header to sort; click again to reverse
- **Dashboard stats** — total monthly cost, active subscription count, and a 12-month annual forecast
- **Annual forecast** — counts actual billing cycles (not calendar days), accounting for end dates and first/last month price overrides
- **First/last month pricing** — optionally set a different price for the first or last billing cycle (e.g. sign-up fee, final discounted payment)
- **Date picker** — start date and end date fields use a native calendar picker
- **Notes** — optional free-text notes per subscription
- **Per-user data isolation** — users see only their own subscriptions and categories
- **Django admin** — full admin panel for superusers
- **Test suite** — 45 tests covering models, views, forecast logic, filters, and data isolation

---

## Tech Stack

| Layer       | Technology              |
|-------------|-------------------------|
| Language    | Python 3.14             |
| Framework   | Django 6.0              |
| Database    | PostgreSQL 15           |
| Container   | Docker & Docker Compose |
| Config      | python-decouple (.env)  |

---

## Project Structure

```
subscription-tracker/
├── config/                  # Django project config (settings, urls, wsgi)
├── subscriptions/           # Main app
│   ├── models.py            # Subscription, Category models
│   ├── views.py             # All views including forecast logic
│   ├── forms.py             # SubscriptionForm, CategoryForm, RegistrationForm
│   ├── urls.py              # App-level URL routing
│   ├── admin.py             # Admin configuration
│   ├── templates/
│   │   ├── base.html        # Base layout with nav and shared CSS
│   │   ├── auth/            # Login, register templates
│   │   └── subscriptions/   # List, create, update, delete, categories
│   └── migrations/
├── seed_demo_data.py        # Creates demo admin + sample subscriptions with categories
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── .env.example             # Environment variable template
```

---

## Quick Start (Docker)

**Requirements:** Docker, Docker Compose

```bash
git clone https://github.com/andriisyniuchenko/subscription-tracker
cd subscription-tracker
```

Copy the environment file and adjust if needed:

```bash
cp .env.example .env
```

Start the project with demo data (build, migrate, seed):

```bash
make demo
```

Open in your browser: **http://localhost:8000**

**Demo credentials:**
| Field    | Value    |
|----------|----------|
| Username | admin    |
| Password | admin123 |

---

## Manual Setup (without Docker)

**Requirements:** Python 3.14+, PostgreSQL

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`) and set your local database credentials and `DB_HOST=localhost`.

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## Environment Variables

All configuration is done via a `.env` file (never committed to git). Use `.env.example` as a template.

| Variable      | Description                        | Example                  |
|---------------|------------------------------------|--------------------------|
| `SECRET_KEY`  | Django secret key                  | `django-insecure-...`    |
| `DEBUG`       | Debug mode (`True` / `False`)      | `True`                   |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts    | `localhost,127.0.0.1`    |
| `DB_NAME`     | PostgreSQL database name           | `subscriptions_db`       |
| `DB_USER`     | PostgreSQL user                    | `postgres`               |
| `DB_PASSWORD` | PostgreSQL password                | `postgres`               |
| `DB_HOST`     | Database host                      | `db` (Docker) / `localhost` |
| `DB_PORT`     | Database port                      | `5432`                   |
| `SESSION_COOKIE_AGE` | Session lifetime in seconds | `1800` (30 min)          |

---

## Make Commands

| Command                   | Description                                      |
|---------------------------|--------------------------------------------------|
| `make demo`               | Full setup: build, migrate, seed demo data       |
| `make test`               | Run the test suite inside the container          |
| `make up`                 | Build and start containers in background         |
| `make down`               | Stop and remove containers and volumes           |
| `make logs`               | Stream web container logs                        |
| `make shell`              | Open Django shell inside the container           |
| `make migrate-docker`     | Run migrations inside the container              |
| `make makemigrations-docker` | Create migrations inside the container        |
| `make superuser`          | Create a superuser inside the container          |
| `make seed`               | Run the demo data seed script                    |
| `make run`                | Run dev server locally (no Docker)               |
| `make migrate`            | Run migrations locally (no Docker)               |

---

## Admin Panel

Available at **http://localhost:8000/admin/** — log in with the superuser account to manage all users, subscriptions, and categories.