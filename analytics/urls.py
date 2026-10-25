from django.urls import path

from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('history/', views.history, name='history'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/reports/', views.reports, name='reports'),
    path('admin/reports/export/', views.reports_export, name='reports_export'),
]
