from decimal import Decimal

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
            'target_audience', 'capacity', 'participation_goal', 'registration_deadline',
        )
        widgets = {
            'start_at': DateTimeInput(),
            'end_at': DateTimeInput(),
            'registration_deadline': DateTimeInput(),
            'description': forms.Textarea(attrs={'rows': 5}),
            'online_url': forms.URLInput(attrs={'placeholder': 'https://…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('start_at', 'end_at', 'registration_deadline'):
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


class EventAIGenerationForm(forms.Form):
    title = forms.CharField(max_length=120)
    category = forms.ChoiceField(choices=EcoCategory.choices)
    start_at = forms.DateTimeField(input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'])
    location = forms.CharField(max_length=160, required=False)
    event_slug = forms.SlugField(max_length=140, required=False)


class EventTagSuggestionForm(forms.Form):
    title = forms.CharField(max_length=120, required=False)
    description = forms.CharField(max_length=3000, required=False)

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('title', '').strip() and not cleaned.get('description', '').strip():
            raise forms.ValidationError('Saisissez un titre ou une description pour suggérer des tags.')
        return cleaned


class CampaignImpactResultForm(StyledFormMixin, forms.Form):
    actual_co2_saved_kg = forms.DecimalField(
        label='CO₂ réellement économisé (kg)', min_value=Decimal('0'),
        max_digits=10, decimal_places=3,
        help_text='Saisissez le résultat mesuré ou documenté après la campagne.',
    )


class EventAttendanceForm(StyledFormMixin, forms.Form):
    attended = forms.ChoiceField(choices=(
        ('unknown', 'À confirmer'),
        ('present', 'Présent·e'),
        ('absent', 'Absent·e'),
    ))


class EventFilterForm(StyledFormMixin, forms.Form):
    WHEN = [('upcoming', 'À venir et en cours'), ('past', 'Passés'), ('all', 'Tous')]

    q = forms.CharField(label='Rechercher', required=False, widget=forms.TextInput(
        attrs={'placeholder': 'Titre, lieu…', 'type': 'search'}))
    kind = forms.ChoiceField(label='Type', required=False, choices=[('', 'Tous')] + Event.Kind.choices)
    category = forms.ChoiceField(label='Catégorie', required=False, choices=[('', 'Toutes')] + EcoCategory.choices)
    format = forms.ChoiceField(label='Format', required=False, choices=[('', 'Tous')] + Event.Format.choices)
    when = forms.ChoiceField(label='Période', required=False, choices=WHEN)
