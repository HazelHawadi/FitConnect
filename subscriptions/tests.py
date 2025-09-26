from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock
from .models import Subscription
import json
import datetime


class SubscriptionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan_name="Pro",
            renewal_date=timezone.now() + datetime.timedelta(days=10),
            active=True,
        )

    def test_str_method(self):
        self.assertEqual(str(self.subscription), "Pro for testuser")

    def test_is_active_true(self):
        self.assertTrue(self.subscription.is_active())

    def test_days_until_renewal(self):
        days = self.subscription.days_until_renewal()
        self.assertIsInstance(days, int)


class PricingViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_pricing_view_renders(self):
        response = self.client.get(reverse("subscriptions:pricing_view"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "subscriptions/pricing.html")
        self.assertIn("plan_benefits", response.context)


class SubscribeViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass", email="test@test.com")
        self.client.login(username="testuser", password="pass")

    @patch("subscriptions.views.stripe.checkout.Session.create")
    def test_subscribe_valid_plan(self, mock_session_create):
        mock_session = MagicMock()
        mock_session.url = "http://stripe-session-url"
        mock_session_create.return_value = mock_session

        response = self.client.get(reverse("subscriptions:subscribe", args=["Pro"]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("stripe-session-url", response.url)

    def test_subscribe_invalid_plan(self):
        response = self.client.get(reverse("subscriptions:subscribe", args=["Invalid"]))
        self.assertRedirects(response, reverse("subscriptions:pricing_view"))


class SubscriptionSuccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.client.login(username="testuser", password="pass")

    def test_subscription_success_renders(self):
        response = self.client.get(reverse("subscriptions:subscription_success"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "subscription/success.html")


class ManageSubscriptionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.client.login(username="testuser", password="pass")
        self.subscription = Subscription.objects.create(
            user=self.user, plan_name="Pro", stripe_subscription_id="sub_123"
        )

    @patch("subscriptions.views.stripe.Subscription.retrieve")
    def test_manage_subscription_with_active(self, mock_retrieve):
        mock_retrieve.return_value = {"cancel_at_period_end": False}
        response = self.client.get(reverse("subscriptions:manage_subscription"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "subscription/manage_subscription.html")
        self.assertIn("subscription", response.context)


class CancelSubscriptionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.client.login(username="testuser", password="pass")
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan_name="Pro",
            stripe_subscription_id="sub_123",
            renewal_date=timezone.now() + datetime.timedelta(days=30),
        )

    @patch("subscriptions.views.stripe.Subscription.modify")
    def test_cancel_subscription_post(self, mock_modify):
        response = self.client.post(reverse("subscriptions:cancel_subscription"))
        self.assertRedirects(response, reverse("subscriptions:manage_subscription"))
        self.subscription.refresh_from_db()
        self.assertFalse(self.subscription.active)


class StripeWebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass")

    @patch("subscriptions.views.stripe.Webhook.construct_event")
    @patch("subscriptions.views.stripe.Subscription.retrieve")
    def test_checkout_session_completed(self, mock_retrieve, mock_construct_event):
        mock_event = {
            "type": "checkout.session.completed",
            "data": {"object": {"metadata": {"user_id": self.user.id, "plan_name": "Pro"}, "subscription": "sub_123"}},
        }
        mock_construct_event.return_value = mock_event
        mock_retrieve.return_value = {
            "id": "sub_123",
            "current_period_start": datetime.datetime.now().timestamp(),
            "current_period_end": (datetime.datetime.now() + datetime.timedelta(days=30)).timestamp(),
            "status": "active",
        }

        response = self.client.post(
            reverse("subscriptions:stripe_webhook"),
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Subscription.objects.filter(user=self.user).exists())

    @patch("subscriptions.views.stripe.Webhook.construct_event")
    def test_invalid_payload(self, mock_construct_event):
        mock_construct_event.side_effect = ValueError("bad payload")
        response = self.client.post(
            reverse("subscriptions:stripe_webhook"),
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
