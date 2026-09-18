from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Order, Product


class StorePageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test-user',
            password='strong-test-password',
        )
        category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            title='Test Product',
            description='A product used by the test suite.',
            price='25.00',
            category=category,
            stock_quantity=10,
        )

    @patch('store.views.get_all_products', return_value=[])
    def test_public_pages_render(self, _get_all_products):
        for name in (
            'home',
            'about',
            'faq',
            'shipping',
            'returns',
            'privacy',
            'terms',
            'subscribe_newsletter',
            'cart',
            'track_order',
        ):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_protected_pages_redirect_anonymous_users(self):
        for name in ('checkout', 'order_tracking', 'order_history', 'address_list', 'account'):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertRedirects(
                    response,
                    f'{reverse("login")}?next={reverse(name)}',
                )

    def test_account_and_address_pages_render_for_authenticated_user(self):
        self.client.login(username='test-user', password='strong-test-password')

        self.assertEqual(self.client.get(reverse('account')).status_code, 200)
        self.assertEqual(self.client.get(reverse('address_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('add_address')).status_code, 200)
        self.assertEqual(self.client.get(reverse('order_history')).status_code, 200)


class CartAndCheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='buyer',
            password='strong-test-password',
        )
        category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            title='Cart Product',
            description='A cart test product.',
            price='12.50',
            category=category,
            stock_quantity=10,
        )
        self.client.login(username='buyer', password='strong-test-password')

    def test_add_to_cart_uses_one_source_of_truth(self):
        response = self.client.post(
            reverse('add_to_cart', args=[self.product.id]),
            {'quantity': 2},
        )
        self.assertRedirects(response, reverse('cart'))

        cart_response = self.client.get(reverse('cart'))
        self.assertEqual(cart_response.status_code, 200)
        self.assertEqual(cart_response.context['total_quantity'], 2)
        self.assertEqual(cart_response.context['total_amount'], 25)
        self.assertEqual(self.client.get(reverse('cart_count_api')).json()['cart_count'], 2)

    def test_checkout_creates_order_and_clears_session_cart(self):
        self.client.post(
            reverse('add_to_cart', args=[self.product.id]),
            {'quantity': 2},
        )

        response = self.client.post(
            reverse('checkout'),
            {'payment_method': 'cash_on_delivery'},
        )

        self.assertEqual(response.status_code, 200)
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.get().quantity, 2)
        self.assertEqual(self.client.session.get('cart'), {'items': {}})
