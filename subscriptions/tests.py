from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from .models import Category, Subscription
from .forms import SubscriptionForm
from .views import _add_months, _annual_forecast, _effective_price, _month_start


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_user(username='testuser', password='testpass123'):
    return User.objects.create_user(username=username, password=password)


def make_sub(user, **kwargs):
    defaults = {
        'name': 'Test Sub',
        'price': Decimal('50.00'),
        'billing_cycle': 'monthly',
        'start_date': date(2026, 1, 1),
        'is_active': True,
    }
    defaults.update(kwargs)
    return Subscription.objects.create(user=user, **defaults)


# ── _add_months ───────────────────────────────────────────────────────────────

class AddMonthsTest(TestCase):

    def test_basic(self):
        self.assertEqual(_add_months(date(2026, 1, 8), 1), date(2026, 2, 8))
        self.assertEqual(_add_months(date(2026, 1, 8), 3), date(2026, 4, 8))

    def test_year_rollover(self):
        self.assertEqual(_add_months(date(2026, 11, 1), 2), date(2027, 1, 1))

    def test_clamps_day_to_month_end(self):
        # Jan 31 + 1 month → Feb 28
        self.assertEqual(_add_months(date(2026, 1, 31), 1), date(2026, 2, 28))


# ── _annual_forecast ──────────────────────────────────────────────────────────

class ForecastTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.today = date(2026, 4, 8)

    def forecast(self, subs):
        return _annual_forecast(subs, today=self.today)

    def test_three_months_with_last_price_override(self):
        """The bug case: $50×2 + $10 last month = $110, not $140."""
        sub = make_sub(
            self.user,
            price=Decimal('50.00'),
            last_month_price=Decimal('10.00'),
            start_date=self.today,
            end_date=_add_months(self.today, 3),
        )
        self.assertEqual(self.forecast([sub]), Decimal('110.00'))

    def test_first_month_price_override(self):
        """First month $120, rest $50 — 3 months total = $220."""
        sub = make_sub(
            self.user,
            price=Decimal('50.00'),
            first_month_price=Decimal('120.00'),
            start_date=self.today,
            end_date=_add_months(self.today, 3),
        )
        self.assertEqual(self.forecast([sub]), Decimal('220.00'))

    def test_both_first_and_last_override(self):
        """First $120, last $10, middle $50 — 4 months = $230."""
        sub = make_sub(
            self.user,
            price=Decimal('50.00'),
            first_month_price=Decimal('120.00'),
            last_month_price=Decimal('10.00'),
            start_date=self.today,
            end_date=_add_months(self.today, 4),
        )
        self.assertEqual(self.forecast([sub]), Decimal('230.00'))

    def test_no_end_date_counts_12_cycles(self):
        """Indefinite subscription → 12 full monthly payments."""
        sub = make_sub(
            self.user,
            price=Decimal('50.00'),
            start_date=self.today,
        )
        self.assertEqual(self.forecast([sub]), Decimal('600.00'))

    def test_inactive_subscription_excluded(self):
        sub = make_sub(self.user, start_date=self.today, is_active=False)
        self.assertEqual(self.forecast([sub]), Decimal('0'))

    def test_already_ended_subscription_excluded(self):
        sub = make_sub(
            self.user,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 4, 1),  # ended before today
        )
        self.assertEqual(self.forecast([sub]), Decimal('0'))

    def test_future_subscription_included(self):
        """Subscription starts next month — all 12 cycles counted."""
        sub = make_sub(
            self.user,
            price=Decimal('30.00'),
            start_date=date(2026, 5, 1),  # starts next month
        )
        self.assertEqual(self.forecast([sub]), Decimal('360.00'))

    def test_past_cycles_skipped(self):
        """Subscription started 2 months ago — only remaining cycles counted."""
        sub = make_sub(
            self.user,
            price=Decimal('50.00'),
            start_date=date(2026, 2, 8),  # started 2 months ago
            end_date=date(2026, 7, 8),    # 5 months total, 3 remaining
        )
        # Remaining payments: Apr 8, May 8, Jun 8 = 3 × $50 = $150
        self.assertEqual(self.forecast([sub]), Decimal('150.00'))

    def test_multiple_subscriptions_summed(self):
        sub1 = make_sub(self.user, name='A', price=Decimal('10.00'), start_date=self.today,
                        end_date=_add_months(self.today, 2))
        sub2 = make_sub(self.user, name='B', price=Decimal('20.00'), start_date=self.today,
                        end_date=_add_months(self.today, 2))
        self.assertEqual(self.forecast([sub1, sub2]), Decimal('60.00'))


# ── _effective_price ──────────────────────────────────────────────────────────

class EffectivePriceTest(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_returns_regular_price_by_default(self):
        sub = make_sub(self.user, price=Decimal('50.00'), start_date=date(2026, 1, 1))
        self.assertEqual(_effective_price(sub, date(2026, 4, 1)), Decimal('50.00'))

    def test_returns_first_month_price_in_start_month(self):
        sub = make_sub(self.user, price=Decimal('50.00'), first_month_price=Decimal('120.00'),
                       start_date=date(2026, 4, 8))
        self.assertEqual(_effective_price(sub, date(2026, 4, 1)), Decimal('120.00'))

    def test_returns_last_month_price_in_end_month(self):
        sub = make_sub(self.user, price=Decimal('50.00'), last_month_price=Decimal('10.00'),
                       start_date=date(2026, 1, 1), end_date=date(2026, 4, 30))
        self.assertEqual(_effective_price(sub, date(2026, 4, 1)), Decimal('10.00'))


# ── Models ────────────────────────────────────────────────────────────────────

class CategoryModelTest(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_str(self):
        cat = Category.objects.create(user=self.user, name='Streaming')
        self.assertEqual(str(cat), 'Streaming')

    def test_unique_per_user(self):
        Category.objects.create(user=self.user, name='Streaming')
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Category.objects.create(user=self.user, name='Streaming')

    def test_same_name_different_users_allowed(self):
        user2 = make_user('other')
        Category.objects.create(user=self.user, name='Streaming')
        Category.objects.create(user=user2, name='Streaming')  # should not raise


class SubscriptionModelTest(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_str(self):
        sub = make_sub(self.user, name='Netflix', price=Decimal('15.99'))
        self.assertEqual(str(sub), 'Netflix - $15.99')

    def test_defaults(self):
        sub = make_sub(self.user)
        self.assertTrue(sub.is_active)
        self.assertEqual(sub.billing_cycle, 'monthly')
        self.assertIsNone(sub.end_date)
        self.assertIsNone(sub.first_month_price)
        self.assertIsNone(sub.last_month_price)
        self.assertEqual(sub.notes, '')


# ── SubscriptionForm validation ───────────────────────────────────────────────

class SubscriptionFormValidationTest(TestCase):

    def setUp(self):
        self.user = make_user()

    def _form(self, **kwargs):
        data = {
            'name': 'Test',
            'price': '50.00',
            'billing_cycle': 'monthly',
            'start_date': '2026-01-01',
        }
        data.update(kwargs)
        return SubscriptionForm(self.user, data)

    def test_valid_form(self):
        self.assertTrue(self._form().is_valid())

    def test_end_date_before_start_date_is_invalid(self):
        form = self._form(start_date='2026-06-01', end_date='2026-01-01')
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)

    def test_end_date_equal_to_start_date_is_invalid(self):
        form = self._form(start_date='2026-01-01', end_date='2026-01-01')
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)

    def test_end_date_after_start_date_is_valid(self):
        form = self._form(start_date='2026-01-01', end_date='2026-06-01')
        self.assertTrue(form.is_valid())

    def test_end_date_optional(self):
        self.assertTrue(self._form(start_date='2026-01-01').is_valid())


# ── Auth views ────────────────────────────────────────────────────────────────

class RegisterViewTest(TestCase):

    def test_register_creates_user_and_redirects(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertRedirects(response, reverse('subscription_list'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_authenticated_user_redirected_away_from_register(self):
        make_user()
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('register'))
        self.assertRedirects(response, reverse('subscription_list'))

    def test_invalid_form_shows_errors(self):
        response = self.client.post(reverse('register'), {
            'username': 'u',
            'password1': 'pass',
            'password2': 'different',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='u').exists())


# ── @login_required ───────────────────────────────────────────────────────────

class LoginRequiredTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.sub = make_sub(self.user)
        self.cat = Category.objects.create(user=self.user, name='Test')

    def assertRedirectsToLogin(self, url):
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_subscription_list_requires_login(self):
        self.assertRedirectsToLogin(reverse('subscription_list'))

    def test_create_subscription_requires_login(self):
        self.assertRedirectsToLogin(reverse('create_subscription'))

    def test_update_subscription_requires_login(self):
        self.assertRedirectsToLogin(reverse('update_subscription', args=[self.sub.pk]))

    def test_delete_subscription_requires_login(self):
        self.assertRedirectsToLogin(reverse('delete_subscription', args=[self.sub.pk]))

    def test_category_list_requires_login(self):
        self.assertRedirectsToLogin(reverse('category_list'))


# ── Subscription CRUD ─────────────────────────────────────────────────────────

class SubscriptionCRUDTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.client.login(username='testuser', password='testpass123')

    def test_list_view_renders(self):
        response = self.client.get(reverse('subscription_list'))
        self.assertEqual(response.status_code, 200)

    def test_create_subscription(self):
        response = self.client.post(reverse('create_subscription'), {
            'name': 'Netflix',
            'price': '15.99',
            'billing_cycle': 'monthly',
            'start_date': '2026-01-01',
        })
        self.assertRedirects(response, reverse('subscription_list'))
        self.assertTrue(Subscription.objects.filter(name='Netflix', user=self.user).exists())

    def test_update_subscription(self):
        sub = make_sub(self.user, name='Old Name')
        response = self.client.post(reverse('update_subscription', args=[sub.pk]), {
            'name': 'New Name',
            'price': '50.00',
            'billing_cycle': 'monthly',
            'start_date': '2026-01-01',
        })
        self.assertRedirects(response, reverse('subscription_list'))
        sub.refresh_from_db()
        self.assertEqual(sub.name, 'New Name')

    def test_delete_subscription(self):
        sub = make_sub(self.user)
        response = self.client.post(reverse('delete_subscription', args=[sub.pk]))
        self.assertRedirects(response, reverse('subscription_list'))
        self.assertFalse(Subscription.objects.filter(pk=sub.pk).exists())

    def test_user_cannot_access_other_users_subscription(self):
        other = make_user('other')
        sub = make_sub(other)
        response = self.client.get(reverse('update_subscription', args=[sub.pk]))
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_other_users_subscription(self):
        other = make_user('other')
        sub = make_sub(other)
        response = self.client.post(reverse('delete_subscription', args=[sub.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Subscription.objects.filter(pk=sub.pk).exists())


# ── Filters ───────────────────────────────────────────────────────────────────

class SubscriptionFilterTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.client.login(username='testuser', password='testpass123')
        self.cat = Category.objects.create(user=self.user, name='Streaming')
        self.sub1 = make_sub(self.user, name='Netflix', category=self.cat, is_active=True)
        self.sub2 = make_sub(self.user, name='Spotify', is_active=False)

    def get_subscriptions(self, params=''):
        response = self.client.get(reverse('subscription_list') + params)
        subs = [s for g in response.context['groups'] for s in g['subscriptions']]
        return subs

    def test_search_by_name(self):
        subs = self.get_subscriptions('?q=netflix')
        self.assertEqual(len(subs), 1)
        self.assertEqual(subs[0].name, 'Netflix')

    def test_search_case_insensitive(self):
        subs = self.get_subscriptions('?q=NETFLIX')
        self.assertEqual(len(subs), 1)

    def test_filter_active(self):
        subs = self.get_subscriptions('?status=active')
        self.assertTrue(all(s.is_active for s in subs))

    def test_filter_inactive(self):
        subs = self.get_subscriptions('?status=inactive')
        self.assertTrue(all(not s.is_active for s in subs))

    def test_filter_by_category(self):
        subs = self.get_subscriptions(f'?category={self.cat.id}')
        self.assertEqual(len(subs), 1)
        self.assertEqual(subs[0].name, 'Netflix')

    def test_no_filter_returns_all(self):
        subs = self.get_subscriptions()
        self.assertEqual(len(subs), 2)


# ── Category views ────────────────────────────────────────────────────────────

class CategoryViewTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.client.login(username='testuser', password='testpass123')

    def test_create_category(self):
        response = self.client.post(reverse('category_list'), {'name': 'Streaming'})
        self.assertRedirects(response, reverse('category_list'))
        self.assertTrue(Category.objects.filter(user=self.user, name='Streaming').exists())

    def test_duplicate_category_shows_form_error_not_500(self):
        Category.objects.create(user=self.user, name='Streaming')
        response = self.client.post(reverse('category_list'), {'name': 'Streaming'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You already have a category with this name.')

    def test_delete_category(self):
        cat = Category.objects.create(user=self.user, name='Streaming')
        response = self.client.post(reverse('delete_category', args=[cat.pk]))
        self.assertRedirects(response, reverse('category_list'))
        self.assertFalse(Category.objects.filter(pk=cat.pk).exists())

    def test_user_cannot_delete_other_users_category(self):
        other = make_user('other')
        cat = Category.objects.create(user=other, name='Streaming')
        response = self.client.post(reverse('delete_category', args=[cat.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Category.objects.filter(pk=cat.pk).exists())

    def test_categories_from_other_user_not_visible(self):
        other = make_user('other')
        Category.objects.create(user=other, name='Other Category')
        Category.objects.create(user=self.user, name='My Category')
        response = self.client.get(reverse('category_list'))
        cats = list(response.context['categories'])
        self.assertEqual(len(cats), 1)
        self.assertEqual(cats[0].name, 'My Category')