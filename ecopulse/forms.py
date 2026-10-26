from decimal import Decimal

from django import forms

from actions.forms import participating_challenges
from actions.models import EcoActionType
from challenges.models import Challenge
from core.forms import DateInput, ImageInput, StyledFormMixin
from core.validators import check_image_format, image_validators


class LocationForm(StyledFormMixin, forms.Form):
    query = forms.CharField(
        label='Ville ou lieu', required=False, max_length=120,
        widget=forms.TextInput(attrs={'placeholder': 'Ex. : Sfax, Lyon, Casablanca…'}),
    )
    latitude = forms.FloatField(
        label='Latitude', required=False, min_value=-90, max_value=90,
        widget=forms.NumberInput(attrs={'step': 'any', 'placeholder': '36.8065'}),
    )
    longitude = forms.FloatField(
        label='Longitude', required=False, min_value=-180, max_value=180,
        widget=forms.NumberInput(attrs={'step': 'any', 'placeholder': '10.1815'}),
    )

    def clean(self):
        cleaned = super().clean()
        lat, lon = cleaned.get('latitude'), cleaned.get('longitude')
        if (lat is None) != (lon is None):
            raise forms.ValidationError('Renseignez la latitude ET la longitude, ou laissez les deux vides.')
        if not cleaned.get('query') and lat is None:
            raise forms.ValidationError('Indiquez une ville ou des coordonnées.')
        return cleaned


class EcoProofForm(StyledFormMixin, forms.Form):
    """Draft sent to EcoProof AI. Same field names as ``actions.forms.SubmissionForm`` so one HTML form feeds both.

    Lenient on purpose: analysing an incomplete draft is the point; the strict rules apply when it is submitted.
    """
    challenge = forms.ModelChoiceField(label='Défi associé', queryset=Challenge.objects.none(), required=False,
                                       empty_label='Aucun défi')
    action_type = forms.ModelChoiceField(label='Action du catalogue', queryset=EcoActionType.objects.none(),
                                         required=False, empty_label='Laisser EcoProof AI proposer')
    performed_on = forms.DateField(label='Date de réalisation', required=False, widget=DateInput())
    quantity = forms.DecimalField(label='Quantité ou mesure', required=False, min_value=Decimal('0.01'),
                                  max_value=Decimal('10000'), decimal_places=2,
                                  widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}))
    description = forms.CharField(
        label='Description de l’action', min_length=10, max_length=1000,
        error_messages={'required': 'Décrivez votre action pour lancer l’analyse.',
                        'min_length': 'Décrivez votre action en quelques mots de plus (10 caractères minimum).'},
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Où, quand, comment ? Quelle quantité ?'}))
    evidence = forms.ImageField(label='Photo justificative', required=False, validators=image_validators,
                                widget=ImageInput())

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['challenge'].queryset = participating_challenges(user).distinct()
        self.fields['action_type'].queryset = EcoActionType.objects.filter(is_active=True)

    def clean_evidence(self):
        return check_image_format(self.cleaned_data.get('evidence'))
