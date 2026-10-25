from datetime import timedelta

from django import forms
from django.conf import settings
from django.utils import timezone

from challenges.models import Challenge, ChallengeParticipation
from core.choices import EcoCategory
from core.forms import DateInput, ImageInput, StyledFormMixin

from .models import ActionSubmission, EcoActionType


class SubmissionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ActionSubmission
        fields = ('action_type', 'challenge', 'performed_on', 'quantity', 'description', 'evidence')
        widgets = {
            'performed_on': DateInput(),
            'evidence': ImageInput(),
            'description': forms.Textarea(attrs={
                'rows': 4, 'placeholder': 'Décrivez précisément ce que vous avez fait : où, quand, comment…'}),
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['action_type'].queryset = EcoActionType.objects.filter(is_active=True)
        self.fields['action_type'].empty_label = 'Choisissez une action du catalogue'
        challenges = Challenge.objects.filter(
            participations__user=user,
            participations__status=ChallengeParticipation.Status.IN_PROGRESS,
            status__in=[Challenge.Status.ACTIVE, Challenge.Status.COMPLETED],
        )
        if self.instance.pk and self.instance.challenge_id:
            challenges = challenges | Challenge.objects.filter(pk=self.instance.challenge_id)
        self.fields['challenge'].queryset = challenges.distinct()
        self.fields['challenge'].empty_label = 'Aucun défi'
        self.fields['challenge'].help_text = 'Seuls les défis auxquels vous participez sont proposés.'
        self.fields['performed_on'].initial = timezone.localdate()

    def clean_performed_on(self):
        day = self.cleaned_data['performed_on']
        today = timezone.localdate()
        if day > today:
            raise forms.ValidationError('La date de réalisation ne peut pas être dans le futur.')
        max_age = settings.ECOTEAMS_SUBMISSION_MAX_AGE_DAYS
        if day < today - timedelta(days=max_age):
            raise forms.ValidationError(f'Seules les actions des {max_age} derniers jours peuvent être déclarées.')
        return day

    def clean(self):
        cleaned = super().clean()
        action_type = cleaned.get('action_type')
        challenge = cleaned.get('challenge')
        day = cleaned.get('performed_on')
        if action_type is None:
            return cleaned
        if action_type.requires_quantity and not cleaned.get('quantity'):
            unit = f' ({action_type.unit})' if action_type.unit else ''
            self.add_error('quantity', f'Indiquez la quantité{unit} pour cette action.')
        if action_type.requires_evidence and not cleaned.get('evidence'):
            self.add_error('evidence', 'Une photo justificative est obligatoire pour cette action.')
        if challenge is not None:
            if challenge.category != action_type.category:
                self.add_error('challenge', 'Cette action ne correspond pas à la catégorie du défi choisi.')
            elif day and not (challenge.start_date <= day <= challenge.end_date):
                self.add_error('performed_on', 'La date doit se situer pendant la période du défi.')
        if day and self.user is not None:
            duplicates = ActionSubmission.objects.filter(
                user=self.user, action_type=action_type, performed_on=day,
            ).exclude(status=ActionSubmission.Status.REJECTED).exclude(pk=self.instance.pk)
            if duplicates.exists():
                self.add_error('performed_on', 'Vous avez déjà déclaré cette action pour cette date.')
        return cleaned


class ModerationForm(StyledFormMixin, forms.Form):
    notes = forms.CharField(
        label='Commentaire / motif', required=False, max_length=1000, widget=forms.Textarea(attrs={'rows': 3}),
        help_text='Obligatoire pour un refus ou une annulation. Visible par l’auteur de la déclaration.',
    )


class ActionTypeForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = EcoActionType
        fields = (
            'name', 'category', 'description', 'points', 'unit', 'co2_factor_kg', 'factor_source',
            'instructions', 'requires_evidence', 'requires_quantity', 'is_active',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'instructions': forms.Textarea(attrs={'rows': 3}),
            'co2_factor_kg': forms.NumberInput(attrs={'step': '0.001', 'min': '0'}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('co2_factor_kg') is not None:
            if not cleaned.get('unit'):
                self.add_error('unit', 'Une unité est nécessaire pour appliquer un facteur CO₂.')
            if not cleaned.get('factor_source', '').strip():
                self.add_error('factor_source', 'Documentez la source du facteur CO₂.')
        return cleaned


class CatalogFilterForm(StyledFormMixin, forms.Form):
    q = forms.CharField(label='Rechercher', required=False, widget=forms.TextInput(
        attrs={'placeholder': 'Nom de l’action…', 'type': 'search'}))
    category = forms.ChoiceField(label='Catégorie', required=False, choices=[('', 'Toutes')] + EcoCategory.choices)
