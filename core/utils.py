from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import slugify


def unique_slugify(instance, value, reserved=(), max_length=80):
    """Return a slug derived from ``value`` that is unique for the model."""
    base = slugify(value)[:max_length].strip('-') or 'element'
    model = type(instance)
    slug = base
    counter = 2
    while slug in reserved or model.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        suffix = f'-{counter}'
        slug = f'{base[:max_length - len(suffix)]}{suffix}'
        counter += 1
    return slug


def name_taken(queryset, field, value, exclude_pk=None):
    """Case-insensitive uniqueness check that also folds accents' case (É == é).

    SQLite's ``iexact`` only folds ASCII letters, so the comparison is done in Python.
    """
    wanted = value.casefold()
    return any(name.casefold() == wanted for name in queryset.exclude(pk=exclude_pk).values_list(field, flat=True))


def percent(value, total):
    if not total:
        return 0
    return max(0, min(100, round(value * 100 / total)))


def safe_next_url(request, default):
    """Return the ``next`` parameter if it points to this site, else ``default``."""
    candidate = request.POST.get('next') or request.GET.get('next')
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return candidate
    return default
