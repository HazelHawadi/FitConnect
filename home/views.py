from django.shortcuts import render, get_object_or_404, redirect
from programs.models import Program
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import ProfileUpdateForm
from programs.models import Booking
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
