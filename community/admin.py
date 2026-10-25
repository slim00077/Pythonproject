from django.contrib import admin
from django.utils import timezone

from .models import Event, EventParticipation


class ParticipationInline(admin.TabularInline):
    model = EventParticipation
    extra = 0
    readonly_fields = ('joined_at',)
    autocomplete_fields = ('user',)


class WhenFilter(admin.SimpleListFilter):
    title = 'date'
    parameter_name = 'when'

    def lookups(self, request, model_admin):
        return (('upcoming', 'À venir'), ('ongoing', 'En cours'), ('past', 'Passés'))

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'upcoming':
            return queryset.filter(start_at__gt=now)
        if self.value() == 'ongoing':
            return queryset.filter(start_at__lte=now, end_at__gte=now)
        if self.value() == 'past':
            return queryset.filter(end_at__lt=now)
        return queryset


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind', 'category', 'format', 'start_at', 'status', 'organizer', 'participant_count')
    list_filter = ('status', 'kind', 'category', 'format', WhenFilter)
    search_fields = ('title', 'description', 'location')
    readonly_fields = ('slug', 'created_at', 'updated_at', 'published_at')
    autocomplete_fields = ('organizer', 'reviewed_by')
    inlines = [ParticipationInline]
    fieldsets = (
        ('À propos', {'fields': ('title', 'slug', 'kind', 'category', 'description', 'target_audience')}),
        ('Lieu et dates', {'fields': ('format', 'location', 'online_url', 'start_at', 'end_at')}),
        ('Participation', {'fields': ('capacity', 'participation_goal')}),
        ('Validation', {'fields': ('status', 'organizer', 'reviewed_by', 'review_notes', 'published_at')}),
    )

    @admin.display(description='participants')
    def participant_count(self, obj):
        return obj.participations.count()


@admin.register(EventParticipation)
class EventParticipationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'team', 'joined_at', 'reminder_sent')
    list_filter = ('event',)
    search_fields = ('user__username', 'event__title')
