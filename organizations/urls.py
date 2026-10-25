from django.urls import path

from . import views

app_name = 'organizations'

urlpatterns = [
    # Member-facing pages
    path('organization/', views.detail, name='detail'),
    path('organization/create/', views.create, name='create'),
    path('organization/settings/', views.settings_view, name='settings'),
    # Association manager workspace
    path('organization/campaigns/', views.campaigns, name='campaigns'),
    path('organization/events/', views.events, name='events'),
    path('organization/proposals/', views.proposals, name='proposals'),
    path('organization/participants/', views.participants, name='participants'),
    path('organization/impact/', views.impact, name='impact'),
    path('organization/history/', views.history, name='history'),
    # Global control center (administrators only)
    path('admin/organizations/', views.admin_list, name='admin_list'),
    path('admin/organizations/create/', views.admin_form, name='admin_create'),
    path('admin/organizations/<int:pk>/edit/', views.admin_form, name='admin_update'),
    path('admin/organizations/<int:pk>/delete/', views.admin_delete, name='admin_delete'),
]
