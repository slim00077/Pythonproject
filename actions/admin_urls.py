from django.urls import path

from . import views

app_name = 'actions_admin'

urlpatterns = [
    path('', views.moderation_list, name='moderation_list'),
    path('types/', views.type_list, name='type_list'),
    path('types/create/', views.type_form, name='type_create'),
    path('types/<int:pk>/edit/', views.type_form, name='type_update'),
    path('types/<int:pk>/toggle/', views.type_toggle, name='type_toggle'),
    path('<int:pk>/', views.moderation_detail, name='moderation_detail'),
]
