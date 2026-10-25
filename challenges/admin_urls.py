from django.urls import path

from . import views

app_name = 'challenges_admin'

urlpatterns = [
    path('', views.review_list, name='review_list'),
    path('<slug:slug>/', views.review_detail, name='review_detail'),
]
