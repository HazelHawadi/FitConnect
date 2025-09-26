from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return ["home", "pricing", "contact_us", "terms_conditions", "privacy_policy"]

    def location(self, item):
        return reverse(item)
