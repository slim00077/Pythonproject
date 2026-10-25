from django import forms
from django.utils import timezone

from core.forms import DateInput, StyledFormMixin

from .models import Goal


class GoalForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Goal
        fields = ('title', 'description', 'category', 'tracking_mode', 'target_value', 'unit', 'current_progress',
                  'start_date', 'deadline')
        widgets = {
            'start_date': DateInput(),
            'deadline': DateInput(),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'tracking_mode': 'En mode automatique, la progression est calculée à partir de vos actions validées '
                             'ou de vos points, sur la période de l’objectif.',
            'current_progress': 'Utilisé uniquement en suivi manuel.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].choices = [('', 'Toutes les catégories')] + list(self.fields['category'].choices)[1:]

    def clean(self):
        cleaned = super().clean()
        start, deadline = cleaned.get('start_date'), cleaned.get('deadline')
        if start and deadline and deadline < start:
            self.add_error('deadline', 'L’échéance doit être postérieure à la date de début.')
        if not self.instance.pk and deadline and deadline < timezone.localdate():
            self.add_error('deadline', 'L’échéance d’un nouvel objectif ne peut pas être dans le passé.')
        mode = cleaned.get('tracking_mode')
        if mode == Goal.TrackingMode.POINTS:
            cleaned['unit'] = 'points'
        elif mode == Goal.TrackingMode.ACTIONS:
            cleaned['unit'] = 'actions'
        return cleaned


class ProgressForm(StyledFormMixin, forms.Form):
    value = forms.IntegerField(label='Nouvelle progression', min_value=0, max_value=100000)
