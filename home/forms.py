from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from allauth.account.forms import SignupForm
from .models import NewsletterSubscriber


class ProfileUpdateForm(UserChangeForm):
    phone_number = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']


class CustomSignupForm(SignupForm):
    subscribe_newsletter = forms.BooleanField(
        required=False,
        label="Subscribe to our newsletter"
    )

    def save(self, request):
        user = super().save(request)
        if self.cleaned_data.get("subscribe_newsletter"):
            NewsletterSubscriber.objects.get_or_create(email=user.email)
        return user

