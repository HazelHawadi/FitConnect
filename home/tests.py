from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core import mail
from home.models import NewsletterSubscriber, ContactMessage
from home.forms import NewsletterForm, ContactForm, CustomSignupForm
from allauth.account.signals import user_signed_up
from datetime import timedelta
import uuid
from programs.models import Program, Booking
from subscriptions.models import Subscription


# -------------------
# Models
# -------------------
class NewsletterSubscriberModelTest(TestCase):
    def test_email_is_normalized_on_save(self):
        sub = NewsletterSubscriber.objects.create(email="  TEST@Email.COM  ")
        self.assertEqual(sub.email, "test@email.com")

    def test_unsubscribe_token_is_unique(self):
        sub1 = NewsletterSubscriber.objects.create(email="user1@example.com")
        sub2 = NewsletterSubscriber.objects.create(email="user2@example.com")
        self.assertNotEqual(sub1.unsubscribe_token, sub2.unsubscribe_token)
        self.assertIsInstance(sub1.unsubscribe_token, uuid.UUID)


class ContactMessageModelTest(TestCase):
    def test_str_representation(self):
        msg = ContactMessage.objects.create(
            name="Alice",
            email="alice@example.com",
            subject="Help Needed",
            message="Test message"
        )
        self.assertEqual(str(msg), "Help Needed from Alice (alice@example.com)")


# -------------------
# Forms
# -------------------
class NewsletterFormTest(TestCase):
    def test_clean_email_rejects_duplicates(self):
        NewsletterSubscriber.objects.create(email="dup@example.com")
        form = NewsletterForm(data={"email": "dup@example.com"})
        self.assertFalse(form.is_valid())
        self.assertIn("This email is already subscribed.", form.errors["email"])


class ContactFormTest(TestCase):
    def test_contact_form_valid(self):
        form = ContactForm(data={
            "name": "Bob",
            "email": "bob@example.com",
            "subject": "Question",
            "message": "Hello there!"
        })
        self.assertTrue(form.is_valid())


class CustomSignupFormTest(TestCase):
    def test_user_subscribed_if_checked(self):
        data = {
            "username": "john",
            "email": "john@example.com",
            "password1": "aStrongPass123",
            "password2": "aStrongPass123",
            "subscribe_newsletter": True,
        }
        form = CustomSignupForm(data)
        self.assertTrue(form.is_valid())
        user = form.save(request=None)
        self.assertTrue(
            NewsletterSubscriber.objects.filter(user=user, email="john@example.com").exists()
        )


# -------------------
# Views
# -------------------
class NewsletterViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("tester", "tester@example.com", "pass123")

    def test_subscribe_success(self):
        response = self.client.post(reverse("newsletter_subscribe"), {"email": "new@example.com"})
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(NewsletterSubscriber.objects.filter(email="new@example.com").exists())

    def test_subscribe_duplicate_email(self):
        NewsletterSubscriber.objects.create(email="dup@example.com")
        response = self.client.post(reverse("newsletter_subscribe"), {"email": "dup@example.com"})
        self.assertRedirects(response, reverse("home"))

    def test_unsubscribe_success(self):
        NewsletterSubscriber.objects.create(email="bye@example.com")
        response = self.client.get(reverse("newsletter_unsubscribe") + "?email=bye@example.com")
        self.assertContains(response, "You have been unsubscribed.")

    def test_unsubscribe_invalid_email(self):
        response = self.client.get(reverse("newsletter_unsubscribe") + "?email=notfound@example.com")
        self.assertContains(response, "not subscribed")

    def test_unsubscribe_no_email(self):
        response = self.client.get(reverse("newsletter_unsubscribe"))
        self.assertContains(response, "No email specified")


class ContactUsViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_contact_post_valid(self):
        response = self.client.post(reverse("contact_us"), {
            "name": "Alice",
            "email": "alice@example.com",
            "subject": "Hello",
            "message": "Test message"
        })
        self.assertRedirects(response, reverse("contact_us"))
        self.assertTrue(ContactMessage.objects.filter(email="alice@example.com").exists())

    def test_contact_post_invalid(self):
        response = self.client.post(reverse("contact_us"), {
            "name": "",
            "email": "invalid",
            "subject": "",
            "message": ""
        })
        self.assertContains(response, "There was an error.")


class StaticViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_privacy_page(self):
        response = self.client.get(reverse("privacy_policy"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home/privacy_content.html")

    def test_terms_page(self):
        response = self.client.get(reverse("terms_conditions"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home/terms_content.html")


class UpdateProfileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="updateuser", email="update@example.com", password="pass123"
        )
        self.client.login(username="updateuser", password="pass123")

    def test_get_update_profile_page(self):
        response = self.client.get(reverse("account_update_profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/update_profile.html")

    def test_post_update_profile_valid(self):
        response = self.client.post(reverse("account_update_profile"), {
            "first_name": "Updated",
            "last_name": "User",
            "username": "updateuser",
            "email": "update@example.com",
            "password": self.user.password,
        })
        self.assertRedirects(response, reverse("account_profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")


class UserDashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="dashuser", email="dash@example.com", password="pass123"
        )
        self.program = Program.objects.create(title="Yoga Class", description="Relaxing class")
        self.client.login(username="dashuser", password="pass123")

    def test_dashboard_with_upcoming_booking_and_subscription(self):
        Booking.objects.create(
            user=self.user,
            program=self.program,
            date=timezone.now() + timedelta(days=1),
        )
        Subscription.objects.create(
            user=self.user,
            plan_name="Pro Plan",
            renewal_date=timezone.now() + timedelta(days=30),
        )

        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/dashboard.html")
        self.assertContains(response, "Yoga Class")
        self.assertContains(response, "Pro Plan")

    def test_dashboard_without_bookings_or_subscription(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No upcoming bookings.")
        self.assertContains(response, "No active subscription.")


# -------------------
# Signals
# -------------------
class SignalsTest(TestCase):
    def test_user_signed_up_creates_subscriber(self):
        user = User.objects.create(username="signaluser", email="signal@example.com")
        user_signed_up.send(sender=User, request=None, user=user)
        self.assertTrue(NewsletterSubscriber.objects.filter(email="signal@example.com").exists())
