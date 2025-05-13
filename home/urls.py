from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.user_dashboard, name='dashboard'),
    path('profile/', views.profile, name='account_profile'),
    path('pricing/', views.pricing, name='pricing'),
    path('update_profile/', views.update_profile, name='account_update_profile'),
]