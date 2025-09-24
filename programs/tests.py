from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch
from datetime import datetime
from .models import Instructor, Program, AvailableDate, Booking, Review
from .forms import BookingForm


# ---------------------
# Instructors
# ---------------------
def create_instructor(name="Test Instructor"):
    return Instructor.objects.create(
        name=name,
        photo="instructors/test.jpg",   # dummy image path
        bio="Experienced trainer",
        rating=4.5,
        email="instr@example.com",
        phone="123-456-7890"
    )


# ---------------------
# Model Tests
# ---------------------
class ProgramModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.instructor = create_instructor()
        cls.program = Program.objects.create(
            title="Yoga Basics",
            description="Beginner yoga program",
            price_per_session=50,
            instructor=cls.instructor,
            image="programs/test.jpg"
        )

    def test_program_str(self):
        self.assertEqual(str(self.program), "Yoga Basics")


class AvailableDateModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        instructor = create_instructor()
        program = Program.objects.create(
            title="Pilates",
            description="Pilates for core strength",
            price_per_session=60,
            instructor=instructor,
            image="programs/test.jpg"
        )
        cls.date = AvailableDate.objects.create(
            program=program,
            date=timezone.now().date(),
            time=timezone.now().time()
        )

    def test_available_date_str(self):
        self.assertIn(str(self.date.date), str(self.date))


class BookingModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="john", password="pass")
        instructor = create_instructor()
        program = Program.objects.create(
            title="Zumba",
            description="Fun dance workout",
            price_per_session=30,
            instructor=instructor,
            image="programs/test.jpg"
        )
        date = AvailableDate.objects.create(
            program=program,
            date=timezone.now().date(),
            time=timezone.now().time()
        )
        cls.booking = Booking.objects.create(
            user=cls.user,
            booking_date=timezone.now(),
            program=program,
            date=date,
            time=date.time,
            sessions=2,
            total_cost=60,
            paid=True
        )

    def test_booking_str(self):
        self.assertIn("john", str(self.booking))
        self.assertIn("Zumba", str(self.booking))


class ReviewModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="alice", password="pass")
        instructor = create_instructor()
        program = Program.objects.create(
            title="Boxing",
            description="Learn to box",
            price_per_session=40,
            instructor=instructor,
            image="programs/test.jpg"
        )
        cls.review = Review.objects.create(
            user=cls.user,
            program=program,
            rating=5,
            comment="Great session!"
        )

    def test_review_str(self):
        self.assertIn("alice", str(self.review))
        self.assertIn("Boxing", str(self.review))


# ---------------------
# Form Tests
# ---------------------
class BookingFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="mike", password="pass")
        instructor = create_instructor()
        self.program = Program.objects.create(
            title="Dance",
            description="Dance program",
            price_per_session=20,
            instructor=instructor,
            image="programs/test.jpg"
        )
        self.date = AvailableDate.objects.create(
            program=self.program,
            date=timezone.now().date(),
            time=timezone.now().time()
        )

    def test_valid_booking_form(self):
        dt = datetime.combine(self.date.date, self.date.time)
        form = BookingForm(
            data={
                "booking_datetime": dt.strftime("%Y-%m-%d %H:%M"),
                "sessions": 2
            },
            program=self.program
        )
        self.assertTrue(form.is_valid())


# ---------------------
# View Tests
# ---------------------
class BookingViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="sara", password="pass")
        self.client.login(username="sara", password="pass")
        self.instructor = create_instructor()
        self.program = Program.objects.create(
            title="HIIT",
            description="High intensity training",
            price_per_session=25,
            instructor=self.instructor,
            image="programs/test.jpg"
        )
        self.date = AvailableDate.objects.create(
            program=self.program,
            date=timezone.now().date(),
            time=timezone.now().time()
        )

    def test_book_program_view_get(self):
        url = reverse("book_program", args=[self.program.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_book_program_view_post_creates_booking(self):
        dt = datetime.combine(self.date.date, self.date.time)
        url = reverse("book_program", args=[self.program.id])
        response = self.client.post(url, {
            "booking_datetime": dt.strftime("%Y-%m-%d %H:%M"),
            "sessions": 1
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Booking.objects.filter(user=self.user).exists())

    @patch("programs.views.stripe.checkout.Session.create")
    def test_confirm_booking_creates_stripe_session(self, mock_stripe):
        mock_stripe.return_value = {"id": "sess_123"}
        booking = Booking.objects.create(
            user=self.user,
            booking_date=timezone.now(),
            program=self.program,
            date=self.date,
            time=self.date.time,
            sessions=1,
            total_cost=25,
            paid=False
        )
        url = reverse("confirm_booking", args=[booking.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_booking_view(self):
        booking = Booking.objects.create(
            user=self.user,
            booking_date=timezone.now(),
            program=self.program,
            date=self.date,
            time=self.date.time,
            sessions=1,
            total_cost=25,
            paid=False
        )
        url = reverse("delete_booking", args=[booking.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("my_bookings"))
        self.assertFalse(Booking.objects.filter(id=booking.id).exists())

    def test_my_bookings_view_lists_user_bookings(self):
        Booking.objects.create(
            user=self.user,
            booking_date=timezone.now(),
            program=self.program,
            date=self.date,
            time=self.date.time,
            sessions=1,
            total_cost=25,
            paid=False
        )
        url = reverse("my_bookings")
        response = self.client.get(url)
        self.assertContains(response, "HIIT")

    def test_update_booking_view(self):
        booking = Booking.objects.create(
            user=self.user,
            booking_date=timezone.now(),
            program=self.program,
            date=self.date,
            time=self.date.time,
            sessions=1,
            total_cost=25,
            paid=False
        )
        dt = datetime.combine(self.date.date, self.date.time)
        url = reverse("update_booking", args=[booking.id])
        response = self.client.post(url, {
            "booking_datetime": dt.strftime("%Y-%m-%d %H:%M"),
            "sessions": 2
        })
        booking.refresh_from_db()
        self.assertEqual(booking.sessions, 2)


class ReviewViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="kate", password="pass")
        self.client.login(username="kate", password="pass")
        instructor = create_instructor()
        self.program = Program.objects.create(
            title="Crossfit",
            description="Strength & conditioning",
            price_per_session=35,
            instructor=instructor,
            image="programs/test.jpg"
        )

    def test_add_review(self):
        url = reverse("add_review", args=[self.program.id])
        response = self.client.post(url, {
            "rating": 5,
            "comment": "Excellent!"
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Review.objects.filter(user=self.user, program=self.program).exists())

    def test_edit_review(self):
        review = Review.objects.create(
            user=self.user,
            program=self.program,
            rating=4,
            comment="Good"
        )
        url = reverse("edit_review", args=[review.id])
        response = self.client.post(url, {
            "rating": 3,
            "comment": "Average"
        })
        review.refresh_from_db()
        self.assertEqual(review.rating, 3)

    def test_delete_review(self):
        review = Review.objects.create(
            user=self.user,
            program=self.program,
            rating=4,
            comment="Nice"
        )
        url = reverse("delete_review", args=[review.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("program_detail", args=[self.program.id]))
        self.assertFalse(Review.objects.filter(id=review.id).exists())
