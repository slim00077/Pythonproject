from django.contrib import admin

from .models import ActionSubmission, EcoActionType, ModerationLog


@admin.register(EcoActionType)
class EcoActionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'points', 'unit', 'co2_factor_kg', 'requires_evidence', 'is_active')
    list_filter = ('category', 'is_active', 'requires_evidence')
    search_fields = ('name', 'description')
    readonly_fields = ('slug', 'created_at', 'updated_at')


class ModerationLogInline(admin.TabularInline):
    model = ModerationLog
    extra = 0
    can_delete = False
    readonly_fields = ('moderator', 'decision', 'previous_status', 'new_status', 'notes', 'points_delta', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ActionSubmission)
class ActionSubmissionAdmin(admin.ModelAdmin):
    """Read-mostly view: approvals must go through the EcoTeams moderation screen
    so that points are recorded by the central scoring service."""

    list_display = ('action_type', 'user', 'performed_on', 'status', 'points_awarded', 'co2_saved_kg', 'reviewed_by')
    list_filter = ('status', 'action_type__category', 'performed_on')
    search_fields = ('user__username', 'description', 'action_type__name')
    readonly_fields = ('status', 'points_awarded', 'co2_saved_kg', 'reviewed_by', 'reviewed_at', 'team',
                       'created_at', 'updated_at')
    inlines = [ModerationLogInline]
    date_hierarchy = 'performed_on'


@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    list_display = ('submission', 'decision', 'moderator', 'points_delta', 'created_at')
    list_filter = ('decision',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
