from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from home import views
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from home.sitemaps import StaticViewSitemap  # You'll create this file

sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('accounts/', include('allauth.urls')),
    path('programs/', include('programs.urls')),
    path('subscription/', include('subscriptions.urls')),
    path('contact/', views.contact_us, name='contact_us'),

    # Google site verification
    path(
        'google5a8e8d4892a3f203.html',
        TemplateView.as_view(
            template_name='google5a8e8d4892a3f203.html',
            content_type='text/html'
        )
    ),

    #robots.txt and sitemap.xml
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("sitemap.xml", sitemap, {'sitemaps': sitemaps}, name='sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
