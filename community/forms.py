from django import forms
from django.utils import timezone

from core.choices import EcoCategory
from core.forms import DateTimeInput, StyledFormMixin

from .models import Event


class EventForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Event
        fields = (
            'title', 'kind', 'category', 'description', 'format', 'location', 'online_url', 'start_at', 'end_at',
            'target_audience', 'capacity', 'participation_goal',
        )
        widgets = {
            'start_at': DateTimeInput(),
            'end_at': DateTimeInput(),
            'description': forms.Textarea(attrs={'rows': 5}),
            'online_url': forms.URLInput(attrs={'placeholder': 'https://…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('start_at', 'end_at'):
            self.fields[name].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M']

    def clean(self):
        cleaned = super().clean()
        end = cleaned.get('end_at')
        if end and end < timezone.now():
            self.add_error('end_at', 'La fin de l’événement ne peut pas être dans le passé.')
        capacity, goal = cleaned.get('capacity'), cleaned.get('participation_goal')
        if capacity and goal and goal > capacity:
            self.add_error('participation_goal', 'L’objectif ne peut pas dépasser la capacité maximale.')
        return cleaned


class EventReviewForm(StyledFormMixin, forms.Form):
    notes = forms.CharField(
        label='Commentaire pour l’organisateur', required=False, max_length=1000,
        widget=forms.Textarea(attrs={'rows': 3}), help_text='Obligatoire en cas de renvoi en brouillon.',
    )


class EventFilterForm(StyledFormMixin, forms.Form):
    WHEN = [('upcoming', 'À venir et en cours'), ('past', 'Passés'), ('all', 'Tous')]

    q = forms.CharField(label='Rechercher', required=False, widget=forms.TextInput(
        attrs={'placeholder': 'Titre, lieu…', 'type': 'search'}))
    kind = forms.ChoiceField(label='Type', required=False, choices=[('', 'Tous')] + Event.Kind.choices)
    category = forms.ChoiceField(label='Catégorie', required=False, choices=[('', 'Toutes')] + EcoCategory.choices)
    format = forms.ChoiceField(label='Format', required=False, choices=[('', 'Tous')] + Event.Format.choices)
    when = forms.ChoiceField(label='Période', required=False, choices=WHEN)
