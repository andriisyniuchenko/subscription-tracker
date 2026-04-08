from django.db import models
from django.contrib.auth.models import User


class Subscription(models.Model):
    BILLING_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    billing_cycle = models.CharField(
        max_length=10,
        choices=BILLING_CHOICES,
        default='monthly'
    )

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - ${self.price}"