import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from subscriptions.models import Category, Subscription


def run():
    # User
    if not User.objects.filter(username="admin").exists():
        user = User.objects.create_superuser(username="admin", password="admin123")
        print("Admin created: admin / admin123")
    else:
        user = User.objects.get(username="admin")
        print("Admin already exists")

    # Categories
    streaming, _ = Category.objects.get_or_create(user=user, name="Streaming")
    healthcare, _ = Category.objects.get_or_create(user=user, name="Healthcare")

    # Subscriptions
    subs = [
        dict(
            name="YouTube Premium",
            price="13.99",
            billing_cycle="monthly",
            category=streaming,
            start_date=date(2024, 1, 1),
            end_date=None,
            is_active=True,
            notes="Family plan",
        ),
        dict(
            name="Netflix",
            price="15.99",
            billing_cycle="monthly",
            category=streaming,
            start_date=date(2023, 6, 1),
            end_date=None,
            is_active=True,
            notes="",
        ),
        dict(
            name="Health Insurance",
            price="49.99",
            billing_cycle="monthly",
            category=healthcare,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            is_active=True,
            notes="Expires end of year",
        ),
    ]

    for data in subs:
        if not Subscription.objects.filter(user=user, name=data["name"]).exists():
            Subscription.objects.create(user=user, **data)
            print(f"Created: {data['name']}")
        else:
            print(f"Already exists: {data['name']}")


if __name__ == "__main__":
    run()