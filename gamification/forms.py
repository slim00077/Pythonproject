from django import forms

from accounts.models import User
from core.forms import StyledFormMixin

from .models import Badge
from .services import MAX_ADJUSTMENT


class BadgeForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Badge
        fields = ('name', 'description', 'icon', 'tone', 'rule', 'category', 'threshold', 'is_active')


class PointAdjustmentForm(StyledFormMixin, forms.Form):
    user = forms.ModelChoiceField(label='Utilisateur', queryset=User.objects.none())
    amount = forms.IntegerField(
        label='Points (positif ou négatif)', min_value=-MAX_ADJUSTMENT, max_value=MAX_ADJUSTMENT,
        help_text='Une correction est une nouvelle écriture : le registre existant n’est jamais modifié.',
    )
    reason = forms.CharField(label='Motif (obligatoire)', max_length=200)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(is_active=True).order_by('username')

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount == 0:
            raise forms.ValidationError('La correction ne peut pas être nulle.')
        return amount
