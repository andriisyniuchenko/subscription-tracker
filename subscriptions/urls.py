from django.urls import path
from .views import subscription_list

urlpatterns = [
    path('', subscription_list, name='subscription_list'),
]