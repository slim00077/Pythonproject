from django import forms

from core.forms import ImageInput, StyledFormMixin
from core.utils import name_taken

from .models import Organization


class _NameUniqueMixin:
    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if name_taken(Organization.objects.all(), 'name', name, exclude_pk=self.instance.pk):
            raise forms.ValidationError('Une organisation porte déjà ce nom.')
        return name


class OrganizationProfileForm(_NameUniqueMixin, StyledFormMixin, forms.ModelForm):
    """Edited by the managers of the organization itself."""

    class Meta:
        model = Organization
        fields = ('name', 'mission', 'focus_area', 'city', 'website', 'contact_email', 'logo')
        widgets = {'logo': ImageInput(), 'mission': forms.Textarea(attrs={'rows': 5})}


class OrganizationAdminForm(_NameUniqueMixin, StyledFormMixin, forms.ModelForm):
    """Administrator form: also controls the type and the activation of the organization."""

    class Meta:
        model = Organization
        fields = ('name', 'kind', 'mission', 'focus_area', 'city', 'website', 'contact_email', 'logo', 'is_active')
        widgets = {'logo': ImageInput(), 'mission': forms.Textarea(attrs={'rows': 4})}


class ParticipantFilterForm(StyledFormMixin, forms.Form):
    q = forms.CharField(label='Rechercher', required=False, widget=forms.TextInput(
        attrs={'placeholder': 'Nom ou identifiant…', 'type': 'search'}))
    event = forms.ModelChoiceField(label='Événement', required=False, queryset=None, empty_label='Tous les événements')

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        from community.models import Event
        self.fields['event'].queryset = Event.objects.filter(organization=organization).order_by('-start_at')
