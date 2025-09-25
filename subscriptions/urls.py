from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('pricing/', views.pricing_view, name='pricing_view'),
    path('subscribe/<str:plan_name>/', views.subscribe, name='subscribe'),
    path('subscription/success/', views.subscription_success, name='subscription_success'),
    path('manage/', views.manage_subscription, name='manage_subscription'),
    path("cancel/", views.cancel_subscription, name="cancel_subscription"),
    path("webhook/", views.stripe_webhook, name="stripe_webhook"),
]
