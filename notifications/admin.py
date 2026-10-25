from django.contrib import admin

from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'kind', 'is_read', 'created_at')
    list_filter = ('kind', 'is_read')
    search_fields = ('title', 'message', 'recipient__username')
    readonly_fields = ('created_at', 'read_at')


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'challenge', 'action', 'points', 'badge', 'goal', 'event', 'leaderboard')
    search_fields = ('user__username',)
