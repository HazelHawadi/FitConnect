from django.utils import timezone
from django.contrib import messages
from .models import Subscription
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from datetime import timedelta

# Create your views here.

@login_required
def subscribe(request, plan_name):
    duration_days = 30
    renewal_date = timezone.now().date() + timedelta(days=duration_days)

    Subscription.objects.update_or_create(
        user=request.user,
        defaults={
            'plan_name': plan_name,
            'renewal_date': renewal_date,
            'active': True,
        }
    )
    return redirect('dashboard')


@login_required
def manage_subscription(request):
    subscription = Subscription.objects.filter(user=request.user).first()

    try:
        if subscription:
            if subscription.stripe_subscription_id:
                if subscription.end_date is None or subscription.end_date > timezone.now():
                    is_active = True
                else:
                    is_active = False
            else:
                is_active = False
                messages.error(request, "No Stripe subscription ID found.")
        else:
            is_active = False
            messages.error(request, "Subscription not found.")
    except Exception as e:
        messages.error(request, f"An error occurred while checking your subscription: {e}")
        is_active = False

    plan_name = subscription.plan_name if subscription else 'Basic'
    subscribe_url = reverse('subscribe', kwargs={'plan_name': plan_name.lower()})

    return render(request, 'subscription/manage_subscription.html', {
        'subscription': subscription,
        'is_active': is_active,
        'subscribe_url': subscribe_url,
    })
