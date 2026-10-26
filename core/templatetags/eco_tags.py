import os
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from core.choices import CATEGORY_ICONS
from core.icons import ICONS
from core.utils import percent as percent_value

register = template.Library()

STATUS_TONES = {
    'pending': 'warning',
    'approved': 'success',
    'rejected': 'danger',
    'draft': 'muted',
    'active': 'success',
    'published': 'success',
    'completed': 'info',
    'archived': 'muted',
    'cancelled': 'danger',
    'in_progress': 'info',
    'abandoned': 'muted',
    'inactive': 'muted',
}


@register.simple_tag
def icon(name, size=20, css=''):
    paths = ICONS.get(name) or ICONS['sparkles']
    return format_html(
        '<svg class="icon {}" width="{}" height="{}" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true" focusable="false">{}</svg>',
        css, size, size, mark_safe(paths),
    )


@register.filter
def category_icon(category):
    return CATEGORY_ICONS.get(category, 'leaf')


@register.filter
def status_tone(status):
    return STATUS_TONES.get(str(status), 'muted')


@register.simple_tag
def percent(value, total):
    return percent_value(value or 0, total or 0)


@register.filter
def initials(user):
    if not user:
        return '?'
    full = (user.get_full_name() or user.username).split()
    return ''.join(part[0] for part in full[:2]).upper() or '?'


@register.filter
def display_name(user):
    if not user:
        return 'Utilisateur supprimé'
    return user.get_full_name() or user.username


@register.filter
def ordinal(value):
    """French ordinal: 1er, 2e, 3e…"""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return value
    return format_html('{}<sup>{}</sup>', number, 'er' if number == 1 else 'e')


@register.filter
def signed(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return value
    return f'+{number}' if number > 0 else str(number)


@register.filter
def get_item(mapping, key):
    try:
        return mapping.get(key)
    except AttributeError:
        return None


@register.inclusion_tag('partials/progress_ring.html')
def progress_ring(value, size=96, stroke=8, label='', tone='lime'):
    value = max(0, min(100, int(value or 0)))
    radius = (size - stroke) / 2
    circumference = 2 * 3.14159265 * radius
    return {
        'value': value,
        'size': size,
        'stroke': stroke,
        'radius': radius,
        'center': size / 2,
        'circumference': round(circumference, 2),
        'offset': round(circumference * (1 - value / 100), 2),
        'label': label,
        'tone': tone,
    }


@register.simple_tag
def asset(path):
    """Static URL with a ``?v=<mtime>`` suffix so browsers never keep serving an outdated CSS/JS file."""
    from django.contrib.staticfiles import finders
    from django.templatetags.static import static
    url = static(path)
    found = finders.find(path)
    if found:
        try:
            return f'{url}?v={int(os.path.getmtime(found))}'
        except OSError:
            pass
    return url
