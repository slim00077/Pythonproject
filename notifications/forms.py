from django import forms

from core.forms import StyledFormMixin

from .models import NotificationPreference


class PreferenceForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = NotificationPreference.KIND_FIELDS
