from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        return [
            'home',
            'dashboard',
            'account_profile',
            'my_bookings',
            'pricing',
            'account_update_profile',
            'delete_account',
            'program_list',
            'instructors_list',
            'contact_us',
        ]

    def location(self, item):
        return reverse(item)
