from django.urls import path
from . import views
from .views import InstructorListView, InstructorDetailView
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
    path('create-checkout-session/<int:program_id>/', views.create_checkout_session, name='create_checkout_session'),
    path('confirm-booking/', views.confirm_booking, name='confirm_booking'),
    path('booking/cache_booking_data/', views.cache_booking_data, name='cache_booking_data'),
    path('booking/success/', views.booking_success, name='booking_success'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('programs/<int:pk>/', views.program_detail, name='program_detail'),
    path('<int:program_id>/review/', views.add_review, name='add_review'),
    path('<int:program_id>/review/delete/', views.delete_review, name='delete_review'),
    path('instructors/', views.InstructorListView.as_view(), name='instructors_list'),
    path('instructors/<int:pk>/', InstructorDetailView.as_view(), name='instructor_detail'),
]
