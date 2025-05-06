from django.urls import path
from . import views
from .views import (
    book_program,
    confirm_booking,
    booking_success,
    create_checkout_session,
)

urlpatterns = [
    path('', views.program_list, name='program_list'),
    path('<int:pk>/', views.program_detail, name='program_detail'),
    path('book/<int:program_id>/', views.book_program, name='book_program'),
    path('create-checkout-session/', create_checkout_session, name='create_checkout_session'),
    path('confirm-booking/', views.confirm_booking, name='confirm_booking'),
    path('booking/success/', views.booking_success, name='booking_success'),
    path('<int:program_id>/review/', views.add_review, name='add_review'),
    path('<int:program_id>/review/delete/', views.delete_review, name='delete_review'),
]
