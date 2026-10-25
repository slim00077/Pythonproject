from django.contrib import admin

from .models import Membership, Team


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    readonly_fields = ('joined_at',)
    autocomplete_fields = ('user',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'captain', 'focus_area', 'status', 'is_open', 'member_count', 'created_at')
    list_filter = ('status', 'focus_area', 'is_open')
    search_fields = ('name', 'motto', 'description', 'captain__username')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    autocomplete_fields = ('captain',)
    inlines = [MembershipInline]
    fieldsets = (
        ('Identité', {'fields': ('name', 'slug', 'motto', 'description', 'logo', 'focus_area')}),
        ('Organisation', {'fields': ('captain', 'status', 'is_open', 'max_members', 'goal_points')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )

    @admin.display(description='membres')
    def member_count(self, obj):
        return obj.memberships.count()


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'role', 'joined_at')
    list_filter = ('role', 'team')
    search_fields = ('user__username', 'team__name')
    autocomplete_fields = ('user', 'team')
