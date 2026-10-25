from django.contrib import admin

from .models import Challenge, ChallengeParticipation


class ParticipationInline(admin.TabularInline):
    model = ChallengeParticipation
    extra = 0
    readonly_fields = ('joined_at', 'completed_at')
    autocomplete_fields = ('user',)


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'status', 'start_date', 'end_date', 'reward_points', 'creator')
    list_filter = ('status', 'category', 'difficulty')
    search_fields = ('title', 'description')
    readonly_fields = ('slug', 'created_at', 'updated_at', 'published_at')
    autocomplete_fields = ('creator', 'reviewed_by')
    inlines = [ParticipationInline]
    date_hierarchy = 'start_date'


@admin.register(ChallengeParticipation)
class ChallengeParticipationAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'team', 'status', 'joined_at', 'completed_at')
    list_filter = ('status', 'challenge')
    search_fields = ('user__username', 'challenge__title')
    readonly_fields = ('joined_at', 'completed_at')
