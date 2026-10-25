"""
URL configuration for the EcoTeams project.

The built-in Django admin lives at ``/django-admin/`` so that the EcoTeams
back-office can use the ``/admin/...`` routes (roles, users, moderation...).
Each application exposes its own ``urls.py`` with an ``app_name`` namespace.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path

from core.views import public_media

admin.site.site_header = 'EcoTeams — Administration Django'
admin.site.site_title = 'EcoTeams'
admin.site.index_title = 'Gestion des données'

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('accounts.urls')),
    path('', include('analytics.urls')),
    path('teams/', include('teams.urls')),
    path('challenges/', include('challenges.urls')),
    path('actions/', include('actions.urls')),
    path('goals/', include('goals.urls')),
    path('', include('gamification.urls')),
    path('community/', include('community.urls')),
    path('notifications/', include('notifications.urls')),
    # Back-office routes of the business modules
    path('admin/challenges/', include('challenges.admin_urls')),
    path('admin/actions/', include('actions.admin_urls')),
    path('admin/events/', include('community.admin_urls')),
]

if settings.DEBUG:
    # Development only; evidence photos are always served through a protected view.
    urlpatterns += [re_path(r'^media/(?P<path>.*)$', public_media)]

handler403 = 'core.views.permission_denied'
handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_error'
