from django import forms
from datetime import datetime, time, timedelta
from .models import AvailableDate, Review

class BookingForm(forms.Form):
    booking_datetime = forms.DateTimeField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'booking_datetime'}),
        input_formats=['%Y-%m-%d %H:%M'],
        required=True
    )
    sessions = forms.IntegerField(min_value=1, initial=1)

    def __init__(self, *args, **kwargs):
        self.program = kwargs.pop('program', None)
        super().__init__(*args, **kwargs)

    def clean_booking_datetime(self):
        dt = self.cleaned_data['booking_datetime']

        # Check for double booking
        if self.program:
            if AvailableDate.objects.filter(program=self.program, date=dt.date(), time=dt.time(), is_booked=True).exists():
                raise forms.ValidationError("This slot is already booked. Please select another time.")

        return dt
    

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']