from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from allauth.account.forms import SignupForm
from .models import NewsletterSubscriber
from .models import ContactMessage


class ProfileUpdateForm(UserChangeForm):
    phone_number = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']


class CustomSignupForm(SignupForm):
    subscribe_newsletter = forms.BooleanField(required=False, label="Subscribe to our newsletter")

    def save(self, request):
        user = super().save(request)
        if self.cleaned_data.get("subscribe_newsletter"):
            NewsletterSubscriber.objects.get_or_create(user=user, defaults={"email": user.email})
        return user


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ["email"]

    def clean_email(self):
        email = self.cleaned_data["email"]
        if NewsletterSubscriber.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already subscribed.")
        return email