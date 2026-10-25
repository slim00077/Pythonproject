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
