from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=100, blank=True, null=True)
    renewal_date = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    benefits = models.JSONField(default=list)

    def __str__(self):
        return f"{self.plan_name} for {self.user.username}"

    def is_valid(self):
        today = timezone.now().date()
        return self.active and (self.end_date is None or self.end_date.date() >= today)

    @property
    def is_active(self):
        return self.is_valid()

    def days_until_renewal(self):
        if not self.renewal_date:
            return None
        return (self.renewal_date.date() - timezone.now().date()).days