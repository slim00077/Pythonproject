from django.urls import path

from . import views

app_name = 'actions'

urlpatterns = [
    path('', views.submission_list, name='list'),
    path('catalog/', views.catalog, name='catalog'),
    path('submit/', views.submission_create, name='create'),
    path('<int:pk>/', views.submission_detail, name='detail'),
    path('<int:pk>/edit/', views.submission_update, name='update'),
    path('<int:pk>/delete/', views.submission_delete, name='delete'),
    path('<int:pk>/evidence/', views.evidence, name='evidence'),
]
