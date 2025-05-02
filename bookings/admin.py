from django.contrib import admin
from .models import Instructor, Program, SessionBooking


admin.site.register(Instructor)
admin.site.register(Program)
admin.site.register(SessionBooking)
