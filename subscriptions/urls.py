from django.urls import path
from .views import (
    subscription_list,
    create_subscription,
    update_subscription,
    delete_subscription,
    category_list,
    delete_category,
)

urlpatterns = [
    path('', subscription_list, name='subscription_list'),
    path('create/', create_subscription, name='create_subscription'),
    path('update/<int:pk>/', update_subscription, name='update_subscription'),
    path('delete/<int:pk>/', delete_subscription, name='delete_subscription'),
    path('categories/', category_list, name='category_list'),
    path('categories/delete/<int:pk>/', delete_category, name='delete_category'),
]