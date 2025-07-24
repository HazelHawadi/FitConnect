from django.urls import path
from . import views

urlpatterns = [
    path('pricing/', views.pricing, name='pricing'),
    path('subscribe/<int:plan_id>/', views.create_checkout_session, name='subscribe'),
    path('checkout-success/', views.checkout_success, name='checkout_success'),
    path('manage/', views.manage_subscription, name='manage_subscription'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
]