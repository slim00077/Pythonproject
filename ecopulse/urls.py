from django.urls import path

from . import views

app_name = 'ecopulse'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('location/', views.set_location, name='location'),
    path('refresh/', views.refresh, name='refresh'),
    path('analysis/', views.ai_analysis, name='analysis'),
    path('proposals/save/', views.save_proposal, name='save_proposal'),
]
