from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta, time
from .models import Program, Instructor, AvailableDate, Booking, Review
from .forms import BookingForm, UpdateBookingForm, ReviewForm
from decimal import Decimal


class ProgramAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.instructor = Instructor.objects.create(
            name="John Doe",
            bio="Experienced instructor",
            rating=4.5,
            email="john@example.com",
            phone="555-555-5555",
            photo="test.jpg"
        )
        self.program = Program.objects.create(
            title="Yoga Basics",
            description="Beginner yoga class",
            price_per_session=Decimal("20.00"),
            instructor=self.instructor,
            image="dummy.jpg"
        )
        self.date = AvailableDate.objects.create(program=self.program, date=timezone.now().date())
        self.booking = Booking.objects.create(
            user=self.user,
            program=self.program,
            date=self.date,
            time=time(14, 0),
            sessions=1,
            total_cost=Decimal("20.00"),
            paid=True
        )
        self.review = Review.objects.create(
            user=self.user,
            program=self.program,
            rating=5,
            comment="Great class!"
        )

    # --- Models ---
    def test_program_str(self):
        self.assertEqual(str(self.program), "Yoga Basics")

    def test_instructor_str(self):
        self.assertEqual(str(self.instructor), "John Doe")

    def test_booking_str(self):
        self.assertEqual(str(self.booking), f"{self.user.username} - {self.program.title}")

    def test_review_str(self):
        self.assertEqual(str(self.review), f"{self.user.username} review on {self.program.title}")

    def test_available_date_str(self):
        self.assertIn(self.program.title, str(self.date))

    # --- Views ---
    def test_program_list_view(self):
        response = self.client.get(reverse('program_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.program.title)

    def test_program_detail_view(self):
        response = self.client.get(reverse('program_detail', args=[self.program.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.program.description)

    def test_booking_flow_authenticated(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('book_program', args=[self.program.id]))
        self.assertEqual(response.status_code, 200)

    def test_booking_flow_redirects_unauthenticated(self):
        response = self.client.get(reverse('book_program', args=[self.program.id]))
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_edit_booking_view(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('edit_booking', args=[self.booking.id]))
        self.assertEqual(response.status_code, 200)

    def test_cancel_booking(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('cancel_booking', args=[self.booking.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Booking.objects.filter(id=self.booking.id).exists())

    def test_add_review_post(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(
            reverse('add_review', args=[self.program.id]),
            {'rating': 4, 'comment': 'Updated comment'}
        )
        self.assertEqual(response.status_code, 302)
        updated_review = Review.objects.get(user=self.user, program=self.program)
        self.assertEqual(updated_review.comment, 'Updated comment')

    def test_delete_review(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('delete_review', args=[self.program.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())

    # --- Forms ---
    def test_valid_booking_form(self):
        future_datetime = timezone.now() + timedelta(days=1)
        form = BookingForm(data={
            'datetime': future_datetime.isoformat(),
            'sessions': 1
        }, program=self.program)
        self.assertTrue(form.is_valid())

    def test_invalid_booking_form_past_date(self):
        past_datetime = timezone.now() - timedelta(days=1)
        form = BookingForm(data={
            'datetime': past_datetime.isoformat(),
            'sessions': 1
        }, program=self.program)
        self.assertFalse(form.is_valid())

    def test_update_booking_form_valid(self):
        future_datetime = timezone.now() + timedelta(days=2)
        form = UpdateBookingForm(data={
            'datetime': future_datetime.isoformat(),
            'sessions': 1
        }, program=self.program, booking_id=self.booking.id)
        self.assertTrue(form.is_valid())

    def test_review_form_valid(self):
        form = ReviewForm(data={
            'rating': 4,
            'comment': 'Nice!'
        })
        self.assertTrue(form.is_valid())
