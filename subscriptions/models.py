from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=100, blank=True, null=True)
    renewal_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    benefits = models.JSONField(default=list)\

    def __str__(self):
        return f"{self.plan_name} for {self.user.username}"

    def is_active(self):
        return self.active and self.renewal_date >= timezone.now().date()

    def days_until_renewal(self):
        return (self.renewal_date - timezone.now().date()).days