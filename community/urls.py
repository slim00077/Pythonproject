from django.urls import path

from . import views

app_name = 'community'

urlpatterns = [
    path('', views.event_list, name='list'),
    path('create/', views.event_create, name='create'),
    path('ai/generate/', views.event_ai_generate, name='ai_generate'),
    path('ai/suggest-tags/', views.event_tag_suggestions, name='tag_suggestions'),
    path('mine/', views.my_events, name='mine'),
    path('<slug:slug>/impact/', views.event_record_impact, name='record_impact'),
    path('<slug:slug>/attendance/', views.event_attendance, name='attendance'),
    path('<slug:slug>/remind-risk/', views.event_send_risk_reminders, name='remind_risk'),
    path('<slug:slug>/', views.event_detail, name='detail'),
    path('<slug:slug>/edit/', views.event_update, name='update'),
    path('<slug:slug>/delete/', views.event_delete, name='delete'),
    path('<slug:slug>/submit/', views.event_submit, name='submit'),
    path('<slug:slug>/join/', views.event_join, name='join'),
    path('<slug:slug>/leave/', views.event_leave, name='leave'),
    path('<slug:slug>/cancel/', views.event_cancel, name='cancel'),
]
