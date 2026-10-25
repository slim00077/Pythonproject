from django.urls import path

from . import views

app_name = 'gamification'

urlpatterns = [
    path('achievements/', views.achievements, name='achievements'),
    path('admin/badges/', views.badge_list, name='badge_list'),
    path('admin/badges/create/', views.badge_form, name='badge_create'),
    path('admin/badges/<int:pk>/edit/', views.badge_form, name='badge_update'),
    path('admin/badges/<int:pk>/delete/', views.badge_delete, name='badge_delete'),
    path('admin/points/', views.ledger, name='ledger'),
    path('admin/points/adjust/', views.adjust, name='adjust'),
]
