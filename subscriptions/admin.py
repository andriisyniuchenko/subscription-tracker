from django.contrib import admin
from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'user',
        'price',
        'billing_cycle',
        'is_active',
        'start_date',
        'created_at',
    )

    list_filter = (
        'billing_cycle',
        'is_active',
        'start_date',
    )

    search_fields = (
        'name',
        'user__username',
    )

    ordering = ('-created_at',)