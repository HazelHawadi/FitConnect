from django.contrib import admin
from .models import Plan, Subscription

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days')
    search_fields = ('name',)
    ordering = ('price',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_name', 'active', 'renewal_date', 'end_date')
    search_fields = ('user__username', 'plan_name')
    list_filter = ('active',)
