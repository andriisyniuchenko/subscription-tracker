from django import forms
from .models import Subscription


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['name', 'price', 'billing_cycle', 'start_date', 'is_active']