from django.contrib import admin

from .models import Badge, PointTransaction, UserBadge


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    """The ledger is append-only: it can be consulted here but never edited."""

    list_display = ('created_at', 'user', 'team', 'amount', 'reason', 'reference', 'created_by')
    list_filter = ('reason', 'team')
    search_fields = ('user__username', 'reference', 'description')
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule', 'category', 'threshold', 'is_active')
    list_filter = ('rule', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('slug', 'created_at', 'updated_at')


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'awarded_at')
    list_filter = ('badge',)
    search_fields = ('user__username',)
    readonly_fields = ('awarded_at',)
