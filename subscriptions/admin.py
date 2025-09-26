from django.contrib import admin
from .models import Subscription

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_name', 'active', 'start_date', 'end_date', 'renewal_date')
    list_filter = ('active', 'plan_name')
    search_fields = ('user__username', 'plan_name')