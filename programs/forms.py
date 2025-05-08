<<<<<<< HEAD
from django import forms
from .models import Review
from .models import AvailableDate

class BookingForm(forms.Form):
    date = forms.ModelChoiceField(queryset=AvailableDate.objects.none(), required=True)
    sessions = forms.IntegerField(min_value=1, initial=1)

    def __init__(self, *args, **kwargs):
        program = kwargs.pop('program', None)
        super().__init__(*args, **kwargs)
        if program:
            self.fields['date'].queryset = AvailableDate.objects.filter(program=program, is_booked=False)

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']

=======
from django import forms
from .models import Review
from .models import AvailableDate

class BookingForm(forms.Form):
    date = forms.ModelChoiceField(queryset=AvailableDate.objects.none(), required=True)
    sessions = forms.IntegerField(min_value=1, initial=1)

    def __init__(self, *args, **kwargs):
        program = kwargs.pop('program', None)
        super().__init__(*args, **kwargs)
        if program:
            self.fields['date'].queryset = AvailableDate.objects.filter(program=program, is_booked=False)

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']

>>>>>>> ba34c1e (Installed required apps)
