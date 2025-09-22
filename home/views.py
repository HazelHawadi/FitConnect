from django.shortcuts import render, get_object_or_404, redirect
from programs.models import Program
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import ProfileUpdateForm, ContactForm, NewsletterForm
from programs.models import Booking
import requests
from django.core.mail import send_mail
from .models import NewsletterSubscriber, ContactMessage
from subscriptions import views
from subscriptions.models import Subscription
from datetime import date
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
import stripe
from django.conf import settings


stripe.api_key = settings.STRIPE_SECRET_KEY


def home(request):
    programs = Program.objects.all()
    return render(request, 'home/index.html', {'programs': programs})


@login_required
def user_dashboard(request):
    user = request.user

    upcoming_bookings = Booking.objects.filter(
        user=user,
        date__date__gte=date.today()
    ).order_by('date__date')[:5]

    subscription = Subscription.objects.filter(user=user).last()

    recent_activity = [
        f"Booked class: {b.program.title} on {b.date.date}" for b in upcoming_bookings
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
    return render(request, 'subscription/pricing.html', {'plans': plans})


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
            # Check if the user already has a subscription
            if request.user.is_authenticated:
                if NewsletterSubscriber.objects.filter(user=request.user).exists():
                    messages.warning(request, "You are already subscribed.")
                else:
                    subscriber = form.save(commit=False)
                    subscriber.user = request.user
                    subscriber.save()
                    messages.success(request, "Thanks for subscribing! 🎉")
            else:
                # For guests
                form.save()
                messages.success(request, "Thanks for subscribing! 🎉")
        else:
            messages.error(request, "This email is already subscribed.")
        return redirect("home")
    

def newsletter_unsubscribe(request):
    email = request.GET.get("email")
    context = {"email": email, "unsubscribed": False}

    if email and NewsletterSubscriber.objects.filter(email=email).exists():
        NewsletterSubscriber.objects.filter(email=email).delete()
        context["unsubscribed"] = True
    else:
        messages.warning(request, "This email was not found in our subscriber list.")

    return render(request, "newsletter_unsubscribed.html", context)