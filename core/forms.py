from django import forms


class StyledFormMixin:
    """Adds the EcoTeams CSS classes to every widget of a form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput,)):
                css = 'checkbox'
            elif isinstance(widget, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
                css = 'choice-list'
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css = 'input select'
            elif isinstance(widget, forms.ClearableFileInput):
                css = 'input file'
            elif isinstance(widget, forms.Textarea):
                css = 'input textarea'
                widget.attrs.setdefault('rows', 4)
            else:
                css = 'input'
            existing = widget.attrs.get('class', '')
            widget.attrs['class'] = f'{existing} {css}'.strip()
            if field.required and not isinstance(widget, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
                widget.attrs.setdefault('aria-required', 'true')
        self._describe_fields()

    def _describe_fields(self, invalid=()):
        """Accessibility: link each input to its help text and error list, flag invalid fields."""
        for name, field in self.fields.items():
            auto_id = self.auto_id % self.add_prefix(name) if '%s' in str(self.auto_id) else ''
            if not auto_id:
                continue
            ids = []
            if field.help_text:
                ids.append(f'{auto_id}_helptext')
            if name in invalid:
                ids.append(f'{auto_id}_errors')
                field.widget.attrs['aria-invalid'] = 'true'
            else:
                field.widget.attrs.pop('aria-invalid', None)
            if ids:
                field.widget.attrs['aria-describedby'] = ' '.join(ids)
            else:
                field.widget.attrs.pop('aria-describedby', None)

    def full_clean(self):
        super().full_clean()
        self._describe_fields(invalid=set(self._errors or ()))


class DateInput(forms.DateInput):
    input_type = 'date'

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format='%Y-%m-%d')


class DateTimeInput(forms.DateTimeInput):
    input_type = 'datetime-local'

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format='%Y-%m-%dT%H:%M')


class ImageInput(forms.ClearableFileInput):
    def __init__(self, attrs=None):
        base = {'accept': 'image/jpeg,image/png,image/webp', 'data-preview': 'true'}
        base.update(attrs or {})
        super().__init__(attrs=base)
