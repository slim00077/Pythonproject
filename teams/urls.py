from django.urls import path

from . import views

app_name = 'teams'

urlpatterns = [
    path('', views.team_list, name='list'),
    path('create/', views.team_create, name='create'),
    path('mine/', views.my_team, name='mine'),
    path('<slug:slug>/', views.team_detail, name='detail'),
    path('<slug:slug>/edit/', views.team_update, name='update'),
    path('<slug:slug>/delete/', views.team_delete, name='delete'),
    path('<slug:slug>/join/', views.team_join, name='join'),
    path('<slug:slug>/leave/', views.team_leave, name='leave'),
    path('<slug:slug>/members/<int:user_id>/remove/', views.member_remove, name='member_remove'),
    path('<slug:slug>/members/<int:user_id>/captain/', views.captain_transfer, name='captain_transfer'),
]
