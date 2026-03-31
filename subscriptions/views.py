from django.shortcuts import render, redirect, get_object_or_404
from .models import Subscription
from .forms import SubscriptionForm, RegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login


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


@login_required
def update_subscription(request, pk):
    subscription = get_object_or_404(
        Subscription,
        id=pk,
        user=request.user
    )

    if request.method == 'POST':
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            return redirect('subscription_list')
    else:
        form = SubscriptionForm(instance=subscription)

    return render(request, 'subscriptions/update.html', {
        'form': form
    })

@login_required
def delete_subscription(request, pk):
    subscription = get_object_or_404(
        Subscription,
        id=pk,
        user=request.user
    )

    if request.method == 'POST':
        subscription.delete()
        return redirect('subscription_list')

    return render(request, 'subscriptions/delete.html', {
        'subscription': subscription
    })


@login_required
def subscription_list(request):
    subscriptions = Subscription.objects.filter(user=request.user)

    total_monthly = sum(
        sub.price if sub.billing_cycle == 'monthly'
        else sub.price / 12
        for sub in subscriptions
        if sub.is_active
    )

    active_count = subscriptions.filter(is_active=True).count()

    return render(request, 'subscriptions/list.html', {
        'subscriptions': subscriptions,
        'total_monthly': round(total_monthly, 2),
        'active_count': active_count,
    })



def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('subscription_list')
    else:
        form = RegistrationForm()

    return render(request, 'auth/register.html', {'form': form})