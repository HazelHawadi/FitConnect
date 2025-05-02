from django.db import models
from django.contrib.auth.models import User


class Instructor(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField()
    photo = models.ImageField(upload_to='instructors/')

    def __str__(self):
        return self.name

class Program(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price_per_session = models.DecimalField(max_digits=6, decimal_places=2)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='programs/')

    def __str__(self):
        return self.title

class AvailableDate(models.Model):
    program = models.ForeignKey(Program, related_name='dates', on_delete=models.CASCADE)
    date = models.DateField()
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.program.title} on {self.date}"

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    date = models.ForeignKey(AvailableDate, on_delete=models.CASCADE)
    sessions = models.IntegerField(default=1)
    total_cost = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.program.title}"
