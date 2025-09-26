from django.contrib import admin
from .sitemaps import StaticViewSitemap
from django.contrib.sitemaps.views import sitemap
from django.urls import path
from . import views

sitemaps = {"static": StaticViewSitemap()}

urlpatterns = [
    path('', views.home, name='home'),
    path("accept-terms/", views.accept_terms, name="accept_terms"),
    path("privacy/", views.privacy_policy, name="privacy_policy"),
    path("terms/", views.terms_conditions, name="terms_conditions"),
    path('dashboard/', views.user_dashboard, name='dashboard'),
    path('profile/', views.profile, name='account_profile'),
    path('pricing/', views.pricing, name='pricing'),
    path('update_profile/', views.update_profile, name='account_update_profile'),
    path('contact/', views.contact_us, name='contact_us'),
    path("newsletter/subscribe/", views.newsletter_subscribe, name="newsletter_subscribe"),
    path("newsletter/unsubscribe/", views.newsletter_unsubscribe, name="newsletter_unsubscribe"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
]