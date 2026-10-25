from django.urls import path

from . import views

app_name = 'challenges'

urlpatterns = [
    path('', views.challenge_list, name='list'),
    path('create/', views.challenge_create, name='create'),
    path('mine/', views.my_challenges, name='mine'),
    path('<slug:slug>/', views.challenge_detail, name='detail'),
    path('<slug:slug>/edit/', views.challenge_update, name='update'),
    path('<slug:slug>/delete/', views.challenge_delete, name='delete'),
    path('<slug:slug>/submit/', views.challenge_submit, name='submit'),
    path('<slug:slug>/join/', views.challenge_join, name='join'),
    path('<slug:slug>/leave/', views.challenge_leave, name='leave'),
    path('<slug:slug>/complete/', views.challenge_complete, name='complete'),
]
