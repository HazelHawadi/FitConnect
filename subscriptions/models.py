from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Plan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration_days = models.IntegerField(default=30)
    features = models.TextField(help_text="Enter one feature per line")

    def __str__(self):
        return self.name

    @property
    def feature_list(self):
        return self.features.strip().split('\n')
 
    
class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=100)
    start_date = models.DateField(null=True, blank=True)
    renewal_date = models.DateField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.plan_name} for {self.user.username}"

    def is_active(self):
        return self.active and self.renewal_date >= timezone.now().date()

    def days_until_renewal(self):
        return (self.renewal_date - timezone.now().date()).days
