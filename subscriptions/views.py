from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from datetime import timedelta
from django.conf import settings
from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt

from .models import Subscription, Plan
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def pricing(request):
    plans = Plan.objects.all()
    return render(request, 'subscription/pricing.html', {'plans': plans})


# Stripe Checkout session creation
@login_required
def create_checkout_session(request, plan_id):
    try:
        plan = Plan.objects.get(id=plan_id)
    except Plan.DoesNotExist:
        messages.error(request, "Selected plan does not exist.")
        return redirect('pricing')

    # Create Stripe Checkout Session
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': plan.name},
                    'unit_amount': int(plan.price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('checkout_success')) + f"?plan_id={plan.id}",
            cancel_url=request.build_absolute_uri(reverse('pricing')),
        )
        return redirect(session.url)
    except Exception as e:
        messages.error(request, f"Stripe error: {e}")
        return redirect('pricing')


@login_required
def checkout_success(request):
    plan_id = request.GET.get('plan_id')

    try:
        plan = Plan.objects.get(id=plan_id)
    except Plan.DoesNotExist:
        messages.error(request, "Plan not found.")
        return redirect('pricing')

    today = timezone.now().date()
    renewal_date = today + timedelta(days=plan.duration_days)

    Subscription.objects.update_or_create(
        user=request.user,
        defaults={
            'plan_name': plan.name,
            'start_date': today,
            'renewal_date': renewal_date,
            'active': True,
            'end_date': None
        }
    )

    messages.success(request, f"Successfully subscribed to the {plan.name} plan.")
    return redirect('manage_subscription')


# Manage Subscription
@login_required
def manage_subscription(request):
    subscription = Subscription.objects.filter(user=request.user).first()

    if request.method == "POST" and 'cancel' in request.POST:
        if subscription:
            subscription.active = False
            subscription.end_date = timezone.now().date()
            subscription.save()
            messages.success(request, "Your subscription has been cancelled.")
            return redirect('manage_subscription')

    is_active = False
    if subscription:
        if subscription.stripe_subscription_id:
            is_active = not subscription.end_date or subscription.end_date > timezone.now().date()
        else:
            is_active = subscription.active
    else:
        messages.error(request, "Subscription not found.")

    subscribe_url = reverse('pricing')

    return render(request, 'subscription/manage_subscription.html', {
        'subscription': subscription,
        'is_active': is_active,
        'subscribe_url': subscribe_url,
    })


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        return HttpResponse(status=400)

    if event['type'] == 'customer.subscription.deleted':
        data = event['data']['object']
        stripe_id = data.get('id')
        subscription = Subscription.objects.filter(stripe_subscription_id=stripe_id).first()
        if subscription:
            subscription.active = False
            subscription.end_date = timezone.now().date()
            subscription.save()

    return HttpResponse(status=200)