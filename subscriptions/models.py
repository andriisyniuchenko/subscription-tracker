from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ['user', 'name']
        ordering = ['name']

    def __str__(self):
        return self.name


class Subscription(models.Model):
    BILLING_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='subscriptions'
    )

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    billing_cycle = models.CharField(
        max_length=10,
        choices=BILLING_CHOICES,
        default='monthly'
    )

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    first_month_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    last_month_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    notes = models.TextField(blank=True, default='')

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - ${self.price}"