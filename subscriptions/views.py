from django.shortcuts import render, redirect
from .models import Subscription
from .forms import SubscriptionForm
from django.contrib.auth.decorators import login_required


@login_required
def subscription_list(request):
    subscriptions = Subscription.objects.filter(user=request.user)

    return render(request, 'subscriptions/list.html', {
        'subscriptions': subscriptions
    })


@login_required
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