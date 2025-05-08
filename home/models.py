from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=100)
    renewal_date = models.DateField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.plan_name} for {self.user.username}"

    def is_active(self):
        return self.active and self.renewal_date >= timezone.now().date()

    def days_until_renewal(self):
        return (self.renewal_date - timezone.now().date()).days
