from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('accounts/register/', views.register, name='register'),
    path('accounts/login/', views.EcoLoginView.as_view(), name='login'),
    path('accounts/logout/', views.EcoLogoutView.as_view(), name='logout'),
    path('accounts/password/', views.EcoPasswordChangeView.as_view(), name='password_change'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('members/<str:username>/', views.public_profile, name='public_profile'),
    # Administration (active superusers only)
    path('admin/roles/', views.role_list, name='role_list'),
    path('admin/roles/create/', views.role_form, name='role_create'),
    path('admin/roles/<int:pk>/edit/', views.role_form, name='role_update'),
    path('admin/roles/<int:pk>/members/', views.role_members, name='role_members'),
    path('admin/roles/<int:pk>/delete/', views.role_delete, name='role_delete'),
    path('admin/users/', views.user_list, name='user_list'),
    path('admin/users/<int:pk>/', views.user_edit, name='user_edit'),
]
