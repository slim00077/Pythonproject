from django import forms

from core.forms import StyledFormMixin


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
