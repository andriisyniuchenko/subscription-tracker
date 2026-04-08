from datetime import date
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

from .models import Subscription, Category
from .forms import SubscriptionForm, CategoryForm, RegistrationForm


def _annual_forecast(subscriptions):
    today = date.today()
    try:
        forecast_end = today.replace(year=today.year + 1)
    except ValueError:
        forecast_end = today.replace(year=today.year + 1, day=28)

    total_days = (forecast_end - today).days
    forecast = Decimal('0')

    for sub in subscriptions:
        if not sub.is_active:
            continue

        period_start = max(sub.start_date, today)
        period_end = min(sub.end_date, forecast_end) if sub.end_date else forecast_end

        if period_end <= period_start:
            continue

        days_active = (period_end - period_start).days
        annual_price = sub.price * 12 if sub.billing_cycle == 'monthly' else sub.price
        forecast += annual_price * Decimal(days_active) / Decimal(total_days)

    return round(forecast, 2)


@login_required
def create_subscription(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.user, request.POST)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.user = request.user
            subscription.save()
            return redirect('subscription_list')
    else:
        form = SubscriptionForm(request.user)

    return render(request, 'subscriptions/create.html', {'form': form})


@login_required
def update_subscription(request, pk):
    subscription = get_object_or_404(Subscription, id=pk, user=request.user)

    if request.method == 'POST':
        form = SubscriptionForm(request.user, request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            return redirect('subscription_list')
    else:
        form = SubscriptionForm(request.user, instance=subscription)

    return render(request, 'subscriptions/update.html', {'form': form})


@login_required
def delete_subscription(request, pk):
    subscription = get_object_or_404(Subscription, id=pk, user=request.user)

    if request.method == 'POST':
        subscription.delete()
        return redirect('subscription_list')

    return render(request, 'subscriptions/delete.html', {'subscription': subscription})


@login_required
def subscription_list(request):
    subscriptions = Subscription.objects.filter(user=request.user).select_related('category')

    total_monthly = sum(
        sub.price if sub.billing_cycle == 'monthly' else sub.price / 12
        for sub in subscriptions
        if sub.is_active
    )
    active_count = sum(1 for sub in subscriptions if sub.is_active)

    # Group subscriptions by category
    groups_dict = {}
    uncategorized = []

    for sub in subscriptions:
        if sub.category_id is None:
            uncategorized.append(sub)
        else:
            cat = sub.category
            if cat.id not in groups_dict:
                groups_dict[cat.id] = {'category': cat, 'subscriptions': []}
            groups_dict[cat.id]['subscriptions'].append(sub)

    groups = sorted(groups_dict.values(), key=lambda g: g['category'].name)

    for group in groups:
        group['monthly_total'] = round(sum(
            s.price if s.billing_cycle == 'monthly' else s.price / 12
            for s in group['subscriptions'] if s.is_active
        ), 2)

    if uncategorized:
        uncat_total = round(sum(
            s.price if s.billing_cycle == 'monthly' else s.price / 12
            for s in uncategorized if s.is_active
        ), 2)
        groups.append({'category': None, 'subscriptions': uncategorized, 'monthly_total': uncat_total})

    return render(request, 'subscriptions/list.html', {
        'groups': groups,
        'total_monthly': round(total_monthly, 2),
        'active_count': active_count,
        'annual_forecast': _annual_forecast(subscriptions),
    })


@login_required
def category_list(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            return redirect('category_list')
    else:
        form = CategoryForm()

    categories = Category.objects.filter(user=request.user)
    return render(request, 'subscriptions/categories.html', {
        'categories': categories,
        'form': form,
    })


@login_required
def delete_category(request, pk):
    category = get_object_or_404(Category, id=pk, user=request.user)
    if request.method == 'POST':
        category.delete()
    return redirect('category_list')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('subscription_list')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('subscription_list')
    else:
        form = RegistrationForm()

    return render(request, 'auth/register.html', {'form': form})