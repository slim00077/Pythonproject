from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import Group, Permission

from core.forms import ImageInput, StyledFormMixin
from core.utils import name_taken

from .models import Role, User

ROLE_PERMISSION_APPS = [
    'teams', 'challenges', 'actions', 'goals', 'gamification', 'community', 'notifications', 'analytics',
]
RESERVED_ROLE_NAMES = {'admin', 'administrateur', 'administrator', 'superuser', 'superutilisateur'}


def assignable_permissions():
    return (
        Permission.objects.filter(content_type__app_label__in=ROLE_PERMISSION_APPS)
        .select_related('content_type')
        .order_by('content_type__app_label', 'content_type__model', 'codename')
    )


class RegisterForm(StyledFormMixin, UserCreationForm):
    """Public sign-up form. It never exposes role or privilege fields."""

    first_name = forms.CharField(label='Prénom', max_length=150)
    last_name = forms.CharField(label='Nom', max_length=150)
    email = forms.EmailField(label='Adresse e-mail')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'organization_type')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Un compte utilise déjà cette adresse e-mail.')
        return email


class LoginForm(StyledFormMixin, AuthenticationForm):
    username = forms.CharField(
        label='Nom d’utilisateur ou e-mail',
        widget=forms.TextInput(attrs={'autofocus': True, 'autocomplete': 'username'}),
    )
    password = forms.CharField(
        label='Mot de passe', strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )

    error_messages = {
        'invalid_login': 'Identifiants incorrects. Vérifiez votre nom d’utilisateur (ou e-mail) et votre mot de passe.',
        'inactive': 'Ce compte est désactivé.',
    }


class ProfileForm(StyledFormMixin, forms.ModelForm):
    """Lets a user edit their own public information — never their privileges."""

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'organization_type', 'organization',
            'city', 'favorite_category', 'skills', 'bio', 'avatar',
        )
        widgets = {'avatar': ImageInput(), 'bio': forms.Textarea(attrs={'rows': 4})}

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Un compte utilise déjà cette adresse e-mail.')
        return email


class StyledPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    pass


class RoleForm(StyledFormMixin, forms.ModelForm):
    """Administrator form for custom roles (Django groups + permissions)."""

    description = forms.CharField(
        label='Description', required=False, max_length=500, widget=forms.Textarea(attrs={'rows': 3})
    )
    permissions = forms.ModelMultipleChoiceField(
        label='Permissions', queryset=Permission.objects.none(), required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Group
        fields = ('name',)
        labels = {'name': 'Nom du rôle'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['permissions'].queryset = assignable_permissions()
        role = getattr(self.instance, 'role', None) if self.instance.pk else None
        self.is_system = bool(role and role.is_system)
        if self.instance.pk:
            self.fields['description'].initial = role.description if role else ''
            self.fields['permissions'].initial = list(self.instance.permissions.values_list('pk', flat=True))
        if self.is_system:
            self.fields['name'].disabled = True
            self.fields['permissions'].disabled = True

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if self.is_system:
            return self.instance.name
        lowered = name.casefold()
        if lowered in RESERVED_ROLE_NAMES or lowered == settings.ECOTEAMS_DEFAULT_ROLE.casefold():
            raise forms.ValidationError('Ce nom est réservé aux niveaux d’accès intégrés.')
        if name_taken(Group.objects.all(), 'name', name, exclude_pk=self.instance.pk):
            raise forms.ValidationError('Un rôle porte déjà ce nom.')
        return name

    def save(self, commit=True):
        group = super().save(commit=True)
        role, _ = Role.objects.get_or_create(group=group)
        role.description = self.cleaned_data.get('description', '')
        role.save()
        if not self.is_system:
            group.permissions.set(self.cleaned_data['permissions'])
        return group


class RoleMembersForm(forms.Form):
    members = forms.ModelMultipleChoiceField(
        label='Membres du rôle', queryset=User.objects.none(), required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, group=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['members'].queryset = User.objects.filter(is_active=True).order_by('username')
        if group is not None and not self.is_bound:
            self.fields['members'].initial = list(group.user_set.values_list('pk', flat=True))


class UserAccessForm(StyledFormMixin, forms.Form):
    """Administrator form to activate an account and choose its roles."""

    is_active = forms.BooleanField(label='Compte actif', required=False)
    groups = forms.ModelMultipleChoiceField(
        label='Rôles', queryset=Group.objects.none(), required=False, widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, target=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['groups'].queryset = Group.objects.order_by('name')
        if target is not None and not self.is_bound:
            self.fields['is_active'].initial = target.is_active
            self.fields['groups'].initial = list(target.groups.values_list('pk', flat=True))
