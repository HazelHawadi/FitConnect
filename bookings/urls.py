from django.urls import path
from . import views

urlpatterns = [
    path('program/<int:program_id>/', views.program_detail, name='program_detail'),
    path('booking/success/', views.booking_success, name='booking_success'),
]
