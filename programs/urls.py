from django.urls import path
from . import views

urlpatterns = [
    path('', views.program_list, name='program_list'),
    path('<int:pk>/', views.program_detail, name='program_detail'),
    path('<int:pk>/book/', views.book_program, name='book_program'),
    path('programs/<int:pk>/book/', views.book_program, name='book_program'),
    path('booking/confirm/', views.confirm_booking, name='confirm_booking'),
    path('<int:program_id>/review/', views.add_review, name='add_review'),
    path('<int:program_id>/review/delete/', views.delete_review, name='delete_review'),
]
