from django.contrib import admin
from .models import Subscription

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan_name", "active", "renewal_date", "stripe_subscription_id")
    list_filter = ("active", "plan_name")
    search_fields = ("user__username", "user__email", "stripe_subscription_id")