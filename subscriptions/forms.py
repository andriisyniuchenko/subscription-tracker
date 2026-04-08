from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Subscription, Category


class SubscriptionForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)
        self.fields['category'].empty_label = 'No category'

    class Meta:
        model = Subscription
        fields = ['name', 'price', 'billing_cycle', 'category', 'start_date', 'end_date',
                  'first_month_price', 'last_month_price', 'notes', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional notes...'}),
        }
        help_texts = {
            'first_month_price': 'Optional. Use if the first billing cycle costs differently (e.g. sign-up fee).',
            'last_month_price': 'Optional. Use if the final billing cycle costs differently (e.g. discounted last payment).',
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date <= start_date:
            self.add_error('end_date', 'End date must be after start date.')

        return cleaned_data


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']