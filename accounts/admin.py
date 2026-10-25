from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Role, User


@admin.register(User)
class EcoUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'organization_type', 'is_staff', 'is_active')
    list_filter = ('organization_type', 'is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (
        ('Profil EcoTeams', {
            'fields': ('organization_type', 'organization', 'city', 'favorite_category', 'skills', 'bio', 'avatar'),
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('group', 'is_system', 'description', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
