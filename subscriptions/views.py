from django.shortcuts import render
from .models import Subscription


def subscription_list(request):
    subscriptions = Subscription.objects.all()

    return render(request, 'subscriptions/list.html', {
        'subscriptions': subscriptions
    })