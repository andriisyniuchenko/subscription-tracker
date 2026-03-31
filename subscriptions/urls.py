from django.urls import path
from .views import subscription_list, create_subscription, update_subscription


urlpatterns = [
    path('', subscription_list, name='subscription_list'),
    path('create/', create_subscription, name='create_subscription'),
    path('update/<int:pk>/', update_subscription, name='update_subscription'),
]