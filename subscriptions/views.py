import calendar as cal
from datetime import date
from decimal import Decimal
from urllib.parse import urlencode

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

from .models import Subscription, Category
from .forms import SubscriptionForm, CategoryForm, RegistrationForm


def _month_start(d):
    return d.replace(day=1)


def _add_months(d, n):
    """Add n months to date d, clamping day to valid range."""
    month = d.month - 1 + n
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, cal.monthrange(year, month)[1])
    return date(year, month, day)


def _effective_price(sub, month_start):
    """Return the price for the current calendar month (used in total_monthly)."""
    if sub.first_month_price is not None and month_start == _month_start(sub.start_date):
        return sub.first_month_price
    if sub.last_month_price is not None and sub.end_date and month_start == _month_start(sub.end_date):
        return sub.last_month_price
    return sub.price


def _annual_forecast(subscriptions, today=None):
    """
    Count actual billing cycles that fall within the next 12 months.
    Each cycle is counted as a full payment (no day-based proration),
    so first/last month overrides apply correctly.
    """
    if today is None:
        today = date.today()
    try:
        forecast_end = today.replace(year=today.year + 1)
    except ValueError:
        forecast_end = today.replace(year=today.year + 1, day=28)

    forecast = Decimal('0')

    for sub in subscriptions:
        if not sub.is_active:
            continue
        if sub.end_date and sub.end_date <= today:
            continue
        if sub.start_date >= forecast_end:
            continue

        if sub.billing_cycle == 'yearly':
            # Yearly stays proportional by days (one big payment per year)
            period_start = max(sub.start_date, today)
            period_end = min(sub.end_date, forecast_end) if sub.end_date else forecast_end
            if period_end > period_start:
                total_days = (forecast_end - today).days
                forecast += sub.price * Decimal((period_end - period_start).days) / Decimal(total_days)
            continue

        # Monthly: count discrete billing cycles
        # Determine total number of payments for this subscription
        if sub.end_date:
            n = 0
            while _add_months(sub.start_date, n + 1) < sub.end_date:
                n += 1
            total_payments = n + 1
        else:
            total_payments = None

        payment_num = 0
        while True:
            period_start = _add_months(sub.start_date, payment_num)
            next_billing = _add_months(sub.start_date, payment_num + 1)

            if total_payments is not None and payment_num >= total_payments:
                break
            if period_start >= forecast_end:
                break
            # Skip billing periods that ended before today (already paid)
            if next_billing <= today:
                payment_num += 1
                continue

            is_first = (payment_num == 0)
            is_last = (total_payments is not None and payment_num == total_payments - 1)

            if is_first and sub.first_month_price is not None:
                price = sub.first_month_price
            elif is_last and sub.last_month_price is not None:
                price = sub.last_month_price
            else:
                price = sub.price

            forecast += price
            payment_num += 1

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


VALID_SORT_FIELDS = {'name', 'price', 'billing_cycle', 'start_date', 'end_date'}


@login_required
def subscription_list(request):
    subscriptions = Subscription.objects.filter(user=request.user).select_related('category')

    # --- Filters ---
    q           = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    status      = request.GET.get('status', '').strip()
    sort        = request.GET.get('sort', 'name').strip()
    direction   = request.GET.get('dir', 'asc').strip()

    if q:
        subscriptions = subscriptions.filter(name__icontains=q)
    if category_id:
        subscriptions = subscriptions.filter(category_id=category_id)
    if status == 'active':
        subscriptions = subscriptions.filter(is_active=True)
    elif status == 'inactive':
        subscriptions = subscriptions.filter(is_active=False)

    # --- Sorting ---
    if sort not in VALID_SORT_FIELDS:
        sort = 'name'
    if direction not in ('asc', 'desc'):
        direction = 'asc'
    subscriptions = subscriptions.order_by(sort if direction == 'asc' else f'-{sort}')

    # --- Stats (on filtered set) ---
    today = date.today()
    total_monthly = sum(
        (_effective_price(sub, _month_start(today)) if sub.billing_cycle == 'monthly' else sub.price / 12)
        for sub in subscriptions if sub.is_active
    )
    active_count = sum(1 for sub in subscriptions if sub.is_active)

    # --- Group by category (preserving sort order within groups) ---
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

    # Base query string for sort links (without sort/dir)
    base_params = {}
    if q:
        base_params['q'] = q
    if category_id:
        base_params['category'] = category_id
    if status:
        base_params['status'] = status
    base_qs = urlencode(base_params)

    return render(request, 'subscriptions/list.html', {
        'groups': groups,
        'total_monthly': round(total_monthly, 2),
        'active_count': active_count,
        'annual_forecast': _annual_forecast(subscriptions),
        'user_categories': Category.objects.filter(user=request.user),
        'filters': {'q': q, 'category': category_id, 'status': status},
        'current_sort': sort,
        'current_dir': direction,
        'base_qs': base_qs,
    })


@login_required
def category_list(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            if Category.objects.filter(user=request.user, name=name).exists():
                form.add_error('name', 'You already have a category with this name.')
            else:
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