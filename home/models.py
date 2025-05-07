from django.db import models
from django.contrib.auth.models import User


class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=100)
    renewal_date = models.DateField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.plan_name} for {self.user.username}"