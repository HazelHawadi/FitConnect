from django.contrib import admin
from .models import Program, Instructor, AvailableDate, Booking


admin.site.register(Program)
admin.site.register(Instructor)
admin.site.register(Booking)
