from django import forms
from .models import Review
from .models import AvailableDate
from .models import Booking
from django.utils import timezone


class BookingForm(forms.Form):
    datetime = forms.DateTimeField(
        widget=forms.TextInput(attrs={'id': 'datetimepicker'}),
        label='Choose Date & Time'
    )
    sessions = forms.IntegerField(min_value=1, max_value=2, initial=1)

    def __init__(self, *args, **kwargs):
        self.program = kwargs.pop('program', None)
        super().__init__(*args, **kwargs)

    def clean_datetime(self):
        datetime = self.cleaned_data['datetime']
        # block past dates
        if datetime < timezone.now():
            raise forms.ValidationError("You cannot book in the past.")

        # Check if someone already booked this slot
        if Booking.objects.filter(program=self.program, time=datetime.time(), date__date=datetime.date()).exists():
            raise forms.ValidationError("This time slot is already booked.")
        return datetime


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']


class UpdateBookingForm(forms.Form):
    datetime = forms.DateTimeField(
        widget=forms.TextInput(attrs={'id': 'datetimepicker'}),
        label='New Date & Time'
    )
    sessions = forms.IntegerField(min_value=1, max_value=2)

    def __init__(self, *args, **kwargs):
        self.program = kwargs.pop('program', None)
        self.booking_id = kwargs.pop('booking_id', None)
        super().__init__(*args, **kwargs)

    def clean_datetime(self):
        datetime = self.cleaned_data['datetime']
        if datetime < timezone.now():
            raise forms.ValidationError("You cannot book in the past.")

        conflict = Booking.objects.filter(
            program=self.program,
            time=datetime.time(),
            date__date=datetime.date()
        ).exclude(id=self.booking_id).exists()

        if conflict:
            raise forms.ValidationError("This time slot is already booked.")
        return datetime