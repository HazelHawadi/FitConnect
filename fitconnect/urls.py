"""fitconnect URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from subscriptions.views import stripe_webhook


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('accounts/', include('allauth.urls')),
    path('', include('programs.urls')),
    path('programs/', include('programs.urls')),
    path('subscription/', include('subscriptions.urls', namespace='subscriptions')),
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),
    path("contact/", TemplateView.as_view(template_name="contact_us.html"), name="contact_us"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)