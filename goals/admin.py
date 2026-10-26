from django.contrib import admin

from .models import Goal, GoalAdvice, GoalProposalRun


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


@admin.register(GoalProposalRun)
class GoalProposalRunAdmin(admin.ModelAdmin):
    list_display = ('pk', 'ambition', 'user', 'status', 'valid_count', 'total_count', 'accepted_count', 'latency_ms',
                    'created_at')
    list_filter = ('status', 'model_name')
    search_fields = ('ambition', 'user__username')
    readonly_fields = [field.name for field in GoalProposalRun._meta.fields]

    @admin.display(description='créées')
    def accepted_count(self, obj):
        return len(obj.accepted)

    def has_add_permission(self, request):
        return False
