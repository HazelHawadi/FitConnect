from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User

class ProfileUpdateForm(UserChangeForm):
    phone_number = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']
