from django.conf import settings
import stripe
from django.utils import timezone
from django.contrib import messages
from .models import Subscription
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from datetime import timedelta

# Create your views here.
stripe.api_key = settings.STRIPE_SECRET_KEY

PLAN_PRICES = {
    'Basic': settings.STRIPE_BASIC_PRICE_ID,
    'Pro': settings.STRIPE_PRO_PRICE_ID,
    'Elite': settings.STRIPE_ELITE_PRICE_ID,
}


@login_required
def subscribe(request, plan_name):
    user = request.user
    price_id = PLAN_PRICES.get(plan_name)

    if not price_id:
        messages.error(request, "Invalid plan selected.")
        return redirect('pricing_view')

    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=user.email,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse('subscriptions:subscription_success')),
            cancel_url=request.build_absolute_uri(reverse('subscriptions:pricing_view')),
        )
        return redirect(checkout_session.url)
    except Exception as e:
        messages.error(request, f"Stripe error: {e}")
        return redirect('subscriptions:pricing_view')


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
    subscribe_url = reverse('subscriptions:subscribe', kwargs={'plan_name': plan_name})

    return render(request, 'subscription/manage_subscription.html', {
        'subscription': subscription,
        'is_active': is_active,
        'subscribe_url': subscribe_url,
    })


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    return HttpResponse(status=200)

def plan_benefits(plan_name):
    return {
        'Basic': [
            "Access to the swimming pool twice per week",
            "Access to sauna once per week",
        ],
        'Pro': [
            "Unlimited access to the swimming pool",
            "Unlimited access to sauna",
            "1 complimentary drink per week",
        ],
        'Elite': [
            "Unlimited access to the swimming pool",
            "Unlimited access to sauna",
            "2 complimentary drinks per week",
            "Personalized training plans",
            "Live & on-demand classes",
        ],
    }.get(plan_name, [])


def pricing_view(request):
    plan_benefits = {
        'Basic': [
            "Access to the swimming pool twice per week",
            "Access to sauna once per week",
        ],
        'Pro': [
            "Unlimited access to the swimming pool",
            "Unlimited access to sauna",
            "1 complimentary drink per week (smoothies/coffee/tea)",
        ],
        'Elite': [
            "Unlimited access to the swimming pool",
            "Unlimited access to sauna",
            "2 complimentary drinks per week (smoothies/coffee/tea)",
            "Personalized training plans",
            "Live & on-demand classes",
        ],
    }

    return render(request, 'subscription/pricing.html', {
        'plan_benefits': plan_benefits
    })


@login_required
def subscription_success(request):
    return render(request, 'subscription/success.html')
