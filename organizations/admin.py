from django.contrib import admin

from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'city', 'is_active', 'created_at')
    list_filter = ('kind', 'is_active', 'focus_area')
    search_fields = ('name', 'city', 'contact_email')
    readonly_fields = ('slug', 'created_at', 'updated_at')
