from django.db import models
from django.contrib.auth.models import User

class Instructor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField()
    image = models.ImageField(upload_to='instructors/')
    specialization = models.CharField(max_length=100)

    def __str__(self):
        return self.user.get_full_name()

class Program(models.Model):
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    duration_minutes = models.PositiveIntegerField()
    price_per_session = models.DecimalField(max_digits=6, decimal_places=2)
    level = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class SessionBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('program', 'date', 'user')
