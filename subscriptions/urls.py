<<<<<<< HEAD
from django.urls import path
from . import views

urlpatterns = [
    path('manage/', views.manage_subscription, name='manage_subscription'),
    path('subscribe/<str:plan_name>/', views.subscribe, name='subscribe'),
=======
from django.urls import path
from . import views

urlpatterns = [
    path('manage/', views.manage_subscription, name='manage_subscription'),
    path('subscribe/<str:plan_name>/', views.subscribe, name='subscribe'),
>>>>>>> ba34c1e (Installed required apps)
]