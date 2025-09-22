from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from .models import NewsletterSubscriber

@receiver(user_signed_up)
def subscribe_newsletter(request, user, **kwargs):
    # Auto-subscribe every new user by default
    NewsletterSubscriber.objects.get_or_create(email=user.email)
