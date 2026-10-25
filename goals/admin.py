from django.contrib import admin

from .models import Goal


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'tracking_mode', 'current_progress', 'target_value', 'deadline', 'status')
    list_filter = ('status', 'tracking_mode', 'category')
    search_fields = ('title', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
