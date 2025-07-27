import stripe
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from programs.models import Instructor, Program, AvailableDate, Booking
from programs.forms import BookingForm
from datetime import date, time, timedelta
from django.utils import timezone
from django.contrib.messages import get_messages


class ProgramTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.instructor = Instructor.objects.create(name='Jane Smith', bio='Certified instructor', rating=4.9)
        self.program = Program.objects.create(
            title='Strength Training',
            description='Build muscle in 6 weeks',
            price_per_session=25.0,
            instructor=self.instructor
        )
        self.available_date = AvailableDate.objects.create(
            program=self.program,
            date=date.today() + timedelta(days=1)
        )
        self.booking_url = reverse('book_program', args=[self.program.id])
        self.program_detail_url = reverse('program_detail', args=[self.program.id])

    # View Tests
    def test_program_list_view(self):
        response = self.client.get(reverse('program_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.program.title)

    def test_program_detail_view(self):
        response = self.client.get(self.program_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.program.description)

    def test_booking_requires_login(self):
        response = self.client.get(self.booking_url)
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_booking_page_authenticated(self):
        self.client.login(username='testuser', password='pass123')
        response = self.client.get(self.booking_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Continue to Confirmation')

    # Model Test
    def test_booking_model_str(self):
        booking = Booking.objects.create(
            user=self.user,
            program=self.program,
            date=self.available_date,
            time=time(10, 0),
            sessions=2,
            total_cost=50.0,
            paid=False
        )
        self.assertEqual(str(booking), f"{self.user.username} - {self.program.title}")

    # Form Test
    def test_booking_form_valid(self):
        future_datetime = timezone.now() + timedelta(days=1)
        form = BookingForm(data={
            'datetime': future_datetime,
            'sessions': 2
        }, program=self.program)
        self.assertTrue(form.is_valid())

    def test_booking_form_invalid(self):
        past_datetime = timezone.now() - timedelta(days=1)
        form = BookingForm(data={
            'datetime': past_datetime,
            'sessions': 0
        }, program=self.program)
        self.assertFalse(form.is_valid())

    # Stripe Mocked Payment Test
    @patch('programs.views.stripe.checkout.Session.create')
    def test_stripe_checkout_session_created(self, mock_stripe_checkout):
        self.client.login(username='testuser', password='pass123')
        mock_stripe_checkout.return_value.id = 'cs_test_123'
        mock_stripe_checkout.return_value.url = 'https://checkout.stripe.com/test_session'

        future_datetime = timezone.now() + timedelta(days=1)
        response = self.client.post(self.booking_url, {
            'datetime': future_datetime,
            'sessions': 2
        })

        self.assertRedirects(response, 'https://checkout.stripe.com/test_session')
        mock_stripe_checkout.assert_called_once()

    # Message Test
    def test_success_message_on_booking_cancel(self):
        self.client.login(username='testuser', password='pass123')
        booking = Booking.objects.create(
            user=self.user,
            program=self.program,
            date=self.available_date,
            time=time(10, 0),
            sessions=1,
            total_cost=25.0,
            paid=False
        )
        cancel_url = reverse('cancel_booking', args=[booking.id])
        response = self.client.post(cancel_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Booking cancelled" in str(m) for m in messages))
