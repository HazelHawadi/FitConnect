from django import forms
from .models import SessionBooking

class SessionBookingForm(forms.ModelForm):
    class Meta:
        model = SessionBooking
        fields = ['date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }