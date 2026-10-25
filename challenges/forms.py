from django import forms
from django.utils import timezone

from core.choices import EcoCategory
from core.forms import DateInput, ImageInput, StyledFormMixin

from .models import MAX_REWARD_POINTS, Challenge


class ChallengeForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Challenge
        fields = (
            'title', 'category', 'difficulty', 'description', 'instructions', 'start_date', 'end_date',
            'duration_days', 'required_actions', 'reward_points', 'image',
        )
        widgets = {
            'start_date': DateInput(),
            'end_date': DateInput(),
            'image': ImageInput(),
            'description': forms.Textarea(attrs={'rows': 4}),
            'instructions': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Une étape par ligne…'}),
        }
        labels = {'reward_points': 'Points de récompense proposés'}

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get('start_date'), cleaned.get('end_date')
        duration = cleaned.get('duration_days')
        if start and end:
            if end < start:
                self.add_error('end_date', 'La date de fin doit être postérieure à la date de début.')
            elif end < timezone.localdate():
                self.add_error('end_date', 'La date de fin ne peut pas être dans le passé.')
            elif duration and duration > (end - start).days + 1:
                self.add_error('duration_days', 'La durée recommandée dépasse la période du défi.')
        return cleaned


class ChallengeReviewForm(StyledFormMixin, forms.Form):
    reward_points = forms.IntegerField(
        label='Points de récompense validés', min_value=0, max_value=MAX_REWARD_POINTS,
        help_text='Vous pouvez ajuster la proposition du créateur avant publication.',
    )
    notes = forms.CharField(
        label='Commentaire pour le créateur', required=False, max_length=1000,
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text='Obligatoire en cas de renvoi en brouillon.',
    )


class ChallengeFilterForm(StyledFormMixin, forms.Form):
    STATUS = [('active', 'En cours'), ('completed', 'Terminés'), ('all', 'Tous')]
    SORTS = [('ending', 'Fin la plus proche'), ('recent', 'Plus récents'), ('points', 'Récompense'),
             ('popular', 'Popularité')]

    q = forms.CharField(label='Rechercher', required=False, widget=forms.TextInput(
        attrs={'placeholder': 'Titre ou description…', 'type': 'search'}))
    category = forms.ChoiceField(label='Catégorie', required=False, choices=[('', 'Toutes')] + EcoCategory.choices)
    difficulty = forms.ChoiceField(label='Difficulté', required=False,
                                   choices=[('', 'Toutes')] + Challenge.Difficulty.choices)
    status = forms.ChoiceField(label='Statut', required=False, choices=STATUS)
    sort = forms.ChoiceField(label='Trier par', required=False, choices=SORTS)
