from django.urls import path

from . import views

app_name = 'goals'

urlpatterns = [
    path('', views.goal_list, name='list'),
    path('create/', views.goal_create, name='create'),
    path('<int:pk>/', views.goal_detail, name='detail'),
    path('<int:pk>/edit/', views.goal_update, name='update'),
    path('<int:pk>/delete/', views.goal_delete, name='delete'),
    path('<int:pk>/progress/', views.goal_progress, name='progress'),
    path('<int:pk>/toggle/', views.goal_toggle, name='toggle'),
]
