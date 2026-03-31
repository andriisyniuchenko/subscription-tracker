import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

def run():
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            password="admin123"
        )
        print("Admin created: admin / admin123")
    else:
        print("Admin already exists")

if __name__ == "__main__":
    run()