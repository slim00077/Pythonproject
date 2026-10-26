from django.urls import path

from . import views

app_name = 'ecoassistant'

urlpatterns = [
    path('assistant/', views.chat, name='chat'),
]

