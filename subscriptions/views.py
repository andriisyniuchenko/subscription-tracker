from django.shortcuts import render, redirect
from .models import Subscription
from .forms import SubscriptionForm


def subscription_list(request):
    subscriptions = Subscription.objects.all()

    return render(request, 'subscriptions/list.html', {
        'subscriptions': subscriptions
    })


def create_subscription(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.user = request.user  # важливо!
            subscription.save()
            return redirect('subscription_list')
    else:
        form = SubscriptionForm()

    return render(request, 'subscriptions/create.html', {
        'form': form
    })