from django import forms

from core.forms import StyledFormMixin

from .models import NotificationPreference


class PreferenceForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = NotificationPreference.KIND_FIELDS


class AnnouncementForm(StyledFormMixin, forms.Form):
    """Administrator broadcast. The audience is chosen server-side from a closed list."""

    AUDIENCES = [
        ('all', 'Tous les comptes actifs'),
        ('student', 'Étudiants et jeunes'),
        ('employee', 'Salariés'),
        ('association', 'Associations'),
        ('organization', 'Les membres d’une organisation'),
    ]

    title = forms.CharField(label='Titre', max_length=140)
    message = forms.CharField(label='Message', max_length=600, widget=forms.Textarea(attrs={'rows': 4}))
    audience = forms.ChoiceField(label='Destinataires', choices=AUDIENCES)
    organization = forms.ModelChoiceField(
        label='Organisation', required=False, queryset=None, empty_label='— Choisir —',
        help_text='Utilisé uniquement avec « Les membres d’une organisation ».',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from organizations.models import Organization
        self.fields['organization'].queryset = Organization.objects.filter(is_active=True).order_by('name')

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('audience') == 'organization' and not cleaned.get('organization'):
            self.add_error('organization', 'Choisissez l’organisation destinataire.')
        return cleaned
