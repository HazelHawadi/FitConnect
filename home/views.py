from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from programs.models import Program
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import ProfileUpdateForm, ContactForm, NewsletterForm
from programs.models import Booking
import requests
from django.core.mail import send_mail
from .models import NewsletterSubscriber, ContactMessage, UserAgreement
from subscriptions import views
from subscriptions.models import Subscription
from datetime import date
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from django.contrib import messages
from django.db import IntegrityError
import stripe
from django.conf import settings


stripe.api_key = settings.STRIPE_SECRET_KEY


def home(request):
    programs = Program.objects.all()
    return render(request, 'home/index.html', {'programs': programs})


@login_required
def accept_terms(request):
    if request.method == "POST":
        agreement, created = UserAgreement.objects.get_or_create(user=request.user)

        # Check which button was clicked
        if "accept_privacy" in request.POST:
            agreement.accepted_privacy = True
            messages.success(request, "You have accepted the Privacy Policy.")
        elif "accept_terms" in request.POST:
            agreement.accepted_terms = True
            messages.success(request, "You have accepted the Terms & Conditions.")

        agreement.save()
    return redirect(request.META.get("HTTP_REFERER", "home"))


def privacy_policy(request):
    return render(request, "privacy_content.html")


def terms_conditions(request):
    return render(request, "terms_content.html")


@login_required
def user_dashboard(request):
    user = request.user

    # Get upcoming bookings
    upcoming_bookings = Booking.objects.filter(
        user=user,
        date__date__gte=date.today()
    ).order_by('date__date')[:5]

    # Get the user's active subscription
    subscription = Subscription.objects.filter(
        user=user,
        active=True
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=timezone.now())
    ).first()

    recent_activity = [
        f"Booked class: {b.program.title} on {b.date.date.strftime('%Y-%m-%d')} at {b.date.time.strftime('%I:%M %p')}"
        for b in upcoming_bookings
    ]

    context = {
        'upcoming_bookings': upcoming_bookings,
        'subscription': subscription,
        'recent_activity': recent_activity,
    }

    return render(request, 'dashboard/dashboard.html', context)


@login_required
def profile(request):
    user = request.user
    try:
        subscription = user.subscription
    except Subscription.DoesNotExist:
        subscription = None
    
    context = {
        'user': user,
        'subscription': subscription,
    }
    return render(request, 'account/account_profile.html', context)


@login_required
def pricing(request):
    plans = [
        {'name': 'Basic', 'price': '$10/month', 'duration_days': 30},
        {'name': 'Pro', 'price': '$25/month', 'duration_days': 30},
        {'name': 'Elite', 'price': '$50/month', 'duration_days': 30},
    ]
    return render(request, 'subscriptions/pricing.html', {'plans': plans})


@login_required
def update_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.instance)
            return redirect('account_profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'account/update_profile.html', {'form': form})


def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()  # Save message in Database
            messages.success(request, "Your message has been sent successfully!")
            return redirect('contact_us')
        else:
            messages.error(request, "There was an error. Please check your input.")
    else:
        form = ContactForm()

    return render(request, 'contact_us.html', {'form': form})


def newsletter_subscribe(request):
    if request.method == "POST":
        form = NewsletterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]

            if request.user.is_authenticated:
                # Block if this user already has a subscription
                if NewsletterSubscriber.objects.filter(user=request.user).exists():
                    messages.warning(request, "You are already subscribed with your account.")
                    return redirect("home")

            try:
                subscriber = form.save(commit=False)
                if request.user.is_authenticated:
                    subscriber.user = request.user
                subscriber.save()
                messages.success(request, "Thanks for subscribing! 🎉")
            except IntegrityError:
                # Catches DB-level duplicate email or duplicate user
                messages.error(request, "This email or user is already subscribed.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

        return redirect("home")
    

def newsletter_unsubscribe(request):
    email = request.GET.get('email', None)

    if email:
        # Remove subscriber if exists
        try:
            subscriber = NewsletterSubscriber.objects.get(email=email)
            subscriber.delete()
            messages.success(request, "You have been unsubscribed.")
        except NewsletterSubscriber.DoesNotExist:
            messages.error(request, "That email is not subscribed.")
    else:
        messages.error(request, "No email specified to unsubscribe.")

    return render(request, 'newsletter_unsubscribed.html', {'email': email})


def robots_txt(request):
    content = render(request, "robots.txt", content_type="text/plain")
    return content