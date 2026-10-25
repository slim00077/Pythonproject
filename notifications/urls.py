from django.urls import path

from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('preferences/', views.preferences, name='preferences'),
    path('read-all/', views.notification_read_all, name='read_all'),
    path('<int:pk>/', views.notification_detail, name='detail'),
    path('<int:pk>/read/', views.notification_read, name='read'),
    path('<int:pk>/delete/', views.notification_delete, name='delete'),
]
