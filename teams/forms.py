from django import forms

from core.choices import EcoCategory
from core.forms import ImageInput, StyledFormMixin
from core.utils import name_taken

from .models import Team


class TeamForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Team
        fields = ('name', 'motto', 'description', 'focus_area', 'logo', 'max_members', 'goal_points', 'is_open', 'status')
        widgets = {
            'logo': ImageInput(),
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['status'].choices = [
                choice for choice in Team.Status.choices if choice[0] != Team.Status.ARCHIVED
            ]
        else:
            del self.fields['status']

    def clean_name(self):
        name = ' '.join(self.cleaned_data['name'].split())
        if name_taken(Team.objects.all(), 'name', name, exclude_pk=self.instance.pk):
            raise forms.ValidationError('Une équipe porte déjà ce nom.')
        return name

    def clean_max_members(self):
        value = self.cleaned_data['max_members']
        if self.instance.pk and value < self.instance.memberships.count():
            raise forms.ValidationError('La limite ne peut pas être inférieure au nombre actuel de membres.')
        return value


class TeamFilterForm(StyledFormMixin, forms.Form):
    SORTS = [('points', 'Points'), ('name', 'Nom'), ('members', 'Membres'), ('recent', 'Plus récentes')]

    q = forms.CharField(label='Rechercher', required=False, widget=forms.TextInput(
        attrs={'placeholder': 'Nom, devise, description…', 'type': 'search'}))
    focus_area = forms.ChoiceField(label='Domaine', required=False, choices=[('', 'Tous les domaines')] + EcoCategory.choices)
    open_only = forms.BooleanField(label='Places disponibles', required=False)
    sort = forms.ChoiceField(label='Trier par', required=False, choices=SORTS)
