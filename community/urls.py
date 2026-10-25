from django.urls import path

from . import views

app_name = 'community'

urlpatterns = [
    path('', views.event_list, name='list'),
    path('create/', views.event_create, name='create'),
    path('mine/', views.my_events, name='mine'),
    path('<slug:slug>/', views.event_detail, name='detail'),
    path('<slug:slug>/edit/', views.event_update, name='update'),
    path('<slug:slug>/delete/', views.event_delete, name='delete'),
    path('<slug:slug>/submit/', views.event_submit, name='submit'),
    path('<slug:slug>/join/', views.event_join, name='join'),
    path('<slug:slug>/leave/', views.event_leave, name='leave'),
    path('<slug:slug>/cancel/', views.event_cancel, name='cancel'),
]
