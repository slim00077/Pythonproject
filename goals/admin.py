from django.contrib import admin

from .models import Goal, GoalAdvice


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'tracking_mode', 'current_progress', 'target_value', 'deadline', 'status')
    list_filter = ('status', 'tracking_mode', 'category')
    search_fields = ('title', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')


@admin.register(GoalAdvice)
class GoalAdviceAdmin(admin.ModelAdmin):
    list_display = ('pk', 'goal', 'user', 'status', 'model_name', 'latency_ms', 'output_tokens', 'helpful', 'created_at')
    list_filter = ('status', 'helpful', 'model_name')
    search_fields = ('goal__title', 'user__username')
    readonly_fields = [field.name for field in GoalAdvice._meta.fields]

    def has_add_permission(self, request):
        return False
