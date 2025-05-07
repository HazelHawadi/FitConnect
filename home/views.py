from django.shortcuts import render
from programs.models import Program
from django.contrib.auth.decorators import login_required
from programs.models import Booking
from .models import Subscription
from datetime import date


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

    try:
        subscription = Subscription.objects.get(user=user, active=True)
    except Subscription.DoesNotExist:
        subscription = None

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
def account_profile(request):
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