from django.utils import timezone
from django.contrib import messages
from .models import Subscription
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from datetime import timedelta, datetime
from django.conf import settings
import stripe
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse


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
        return redirect('subscriptions:pricing_view')

    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=user.email,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.build_absolute_uri(
                reverse('subscriptions:subscription_success')
            ) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.build_absolute_uri(reverse('subscriptions:pricing_view')),
            metadata={
                "user_id": user.id,
                "plan_name": plan_name,
            },
        )
        return redirect(checkout_session.url, code=303)

    except Exception as e:
        messages.error(request, f"Stripe error: {e}")
        return redirect('subscriptions:pricing_view')


@login_required
def manage_subscription(request):
    subscription = Subscription.objects.filter(user=request.user).first()

    if subscription:
        try:
            is_active = subscription.is_active()
            if not subscription.stripe_subscription_id:
                messages.error(request, "No Stripe subscription ID found.")
        except Exception as e:
            messages.error(request, f"An error occurred while checking your subscription: {e}")
            is_active = False
    else:
        subscription = None
        is_active = False
        messages.error(request, "Subscription not found.")

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
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return JsonResponse({'error': 'Invalid payload/signature'}, status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata'].get('user_id')
        plan_name = session['metadata'].get('plan_name')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        stripe_sub = stripe.Subscription.retrieve(session['subscription'])

        period_start = datetime.fromtimestamp(stripe_sub['current_period_start'], tz=timezone.utc).date()
        period_end = datetime.fromtimestamp(stripe_sub['current_period_end'], tz=timezone.utc).date()

        Subscription.objects.update_or_create(
            user=user,
            defaults={
                "plan_name": plan_name,
                "stripe_subscription_id": stripe_sub.id,
                "start_date": period_start,
                "end_date": period_end,
                "renewal_date": period_end,
                "active": stripe_sub['status'] in ["active", "trialing"],
                "benefits": plan_benefits(plan_name),
            }
        )

    elif event['type'] == 'customer.subscription.updated':
        sub = event['data']['object']
        subscription = Subscription.objects.filter(stripe_subscription_id=sub['id']).first()
        if subscription:
            period_start = datetime.fromtimestamp(sub['current_period_start'], tz=timezone.utc).date()
            period_end = datetime.fromtimestamp(sub['current_period_end'], tz=timezone.utc).date()
            subscription.start_date = period_start
            subscription.end_date = period_end
            subscription.renewal_date = period_end
            subscription.active = sub['status'] in ["active", "trialing"]
            subscription.save()

    elif event['type'] == 'customer.subscription.deleted':
        sub = event['data']['object']
        Subscription.objects.filter(stripe_subscription_id=sub['id']).update(
            active=False,
            end_date=datetime.fromtimestamp(sub['current_period_end'], tz=timezone.utc).date()
        )

    return JsonResponse({'status': 'success'})


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


@login_required
def change_plan(request):
    subscription = Subscription.objects.filter(user=request.user).first()
    if not subscription or not subscription.active:
        messages.error(request, "No active subscription found.")
        return redirect('subscriptions:manage_subscription')

    if request.method == "POST":
        new_plan = request.POST.get("plan")
        current_plan = subscription.plan_name

        if new_plan == current_plan:
            messages.info(request, "You are already on this plan.")
            return redirect('subscriptions:manage_subscription')

        # Upgrade logic
        plan_order = ["Basic", "Pro", "Elite"]
        if plan_order.index(new_plan) > plan_order.index(current_plan):
            # Call Stripe to update subscription immediately (user pays difference)
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    'id': stripe.Subscription.retrieve(subscription.stripe_subscription_id)['items']['data'][0].id,
                    'price': PLAN_PRICES[new_plan],
                }],
                proration_behavior='create_prorations'
            )
            messages.success(request, f"Successfully upgraded to {new_plan}!")
        
        else:
            # Downgrade only allow after end of period
            messages.warning(request, f"You can only downgrade to {new_plan} after your current cycle ends.")
        
        return redirect('subscriptions:manage_subscription')

    return render(request, "subscription/change_plan.html", {
        "current_plan": subscription.plan_name,
        "plans": PLAN_PRICES.keys(),
    })