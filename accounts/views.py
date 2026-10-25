from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy

from analytics.activity import log_activity
from analytics.models import ActivityLog
from core.decorators import superuser_required
from core.permissions import BACKOFFICE_PERMISSIONS
from gamification.models import UserBadge
from gamification.services import compute_streaks, user_points
from notifications.models import Notification
from notifications.services import notify
from teams.models import Membership
from teams.services import get_membership

from .forms import LoginForm, ProfileForm, RegisterForm, RoleForm, RoleMembersForm, StyledPasswordChangeForm, UserAccessForm
from .models import Role, User
from .services import get_default_role_group

ACTION_LABELS = {'add': 'Peut ajouter', 'change': 'Peut modifier', 'delete': 'Peut supprimer', 'view': 'Peut consulter'}


def register(request):
    if request.user.is_authenticated:
        return redirect('analytics:dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
        messages.success(request, f'Bienvenue sur EcoTeams, {user.display_name} ! Rejoignez une équipe pour commencer.')
        return redirect('analytics:dashboard')
    return render(request, 'accounts/register.html', {'form': form})


class EcoLoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        if self.request.user.is_superuser:
            return reverse('analytics:admin_dashboard')
        return reverse('analytics:dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Bon retour parmi nous, {form.get_user().display_name} !')
        return response


class EcoLogoutView(auth_views.LogoutView):
    """Django 5 only accepts POST for logout, which protects it with CSRF."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, 'Vous êtes déconnecté·e. À bientôt !')
        return response


class EcoPasswordChangeView(SuccessMessageMixin, auth_views.PasswordChangeView):
    template_name = 'accounts/password_change.html'
    form_class = StyledPasswordChangeForm
    success_url = reverse_lazy('accounts:profile')
    success_message = 'Votre mot de passe a été modifié.'


def _profile_context(user):
    return {
        'profile_user': user,
        'membership': get_membership(user),
        'points': user_points(user),
        'badges': UserBadge.objects.filter(user=user).select_related('badge'),
        'streak': compute_streaks(user),
        'approved_actions': user.action_submissions.filter(status='approved').count(),
        'completed_challenges': user.challenge_participations.filter(status='completed').count(),
    }


@login_required
def profile(request):
    context = _profile_context(request.user)
    context['activities'] = ActivityLog.objects.filter(actor=request.user)[:8]
    context['roles'] = request.user.groups.order_by('name')
    context['is_own'] = True
    return render(request, 'accounts/profile.html', context)


@login_required
def public_profile(request, username):
    user = get_object_or_404(User, username=username, is_active=True)
    if user == request.user:
        return redirect('accounts:profile')
    context = _profile_context(user)
    context['is_own'] = False
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profil mis à jour.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile_edit.html', {'form': form})


# --- Administration: roles and users (superuser only) ----------------------------

def _permission_label(permission):
    action = permission.codename.split('_', 1)[0]
    model = permission.content_type.model_class()
    if action in ACTION_LABELS and model is not None and permission.codename == f'{action}_{model._meta.model_name}':
        return f'{ACTION_LABELS[action]} : {model._meta.verbose_name}'
    return permission.name


def _permission_groups(form):
    selected = {str(value) for value in (form['permissions'].value() or [])}
    grouped = {}
    for permission in form.fields['permissions'].queryset:
        app_label = permission.content_type.app_label
        key = f'{app_label}.{permission.codename}'
        grouped.setdefault(apps.get_app_config(app_label).verbose_name, []).append({
            'id': permission.pk,
            'label': _permission_label(permission),
            'checked': str(permission.pk) in selected,
            'key': key in BACKOFFICE_PERMISSIONS,
        })
    for items in grouped.values():
        items.sort(key=lambda item: (not item['key'], item['label']))
    return list(grouped.items())


@superuser_required
def role_list(request):
    groups = (
        Group.objects.select_related('role')
        .annotate(member_total=Count('user', distinct=True), permission_total=Count('permissions', distinct=True))
        .order_by('name')
    )
    roles = sorted(groups, key=lambda g: (not getattr(getattr(g, 'role', None), 'is_system', False), g.name.lower()))
    return render(request, 'accounts/admin/role_list.html', {
        'roles': roles,
        'superusers': User.objects.filter(is_superuser=True, is_active=True),
        'default_role': settings.ECOTEAMS_DEFAULT_ROLE,
    })


@superuser_required
def role_form(request, pk=None):
    group = get_object_or_404(Group, pk=pk) if pk else None
    form = RoleForm(request.POST or None, instance=group)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            saved = form.save()
            log_activity(request.user, ActivityLog.Verb.ROLE_CHANGED,
                         f'Rôle « {saved.name} » {"créé" if group is None else "modifié"}.', team=None)
        messages.success(request, f'Rôle « {saved.name} » enregistré.')
        return redirect('accounts:role_list')
    return render(request, 'accounts/admin/role_form.html', {
        'form': form, 'group': group, 'permission_groups': _permission_groups(form), 'is_system': form.is_system,
    })


@superuser_required
def role_members(request, pk):
    group = get_object_or_404(Group, pk=pk)
    role = Role.objects.filter(group=group).first()
    if role and role.is_system:
        messages.info(request, 'Le rôle par défaut est attribué automatiquement à tous les comptes.')
        return redirect('accounts:role_list')
    form = RoleMembersForm(request.POST or None, group=group)
    if request.method == 'POST' and form.is_valid():
        before = set(group.user_set.values_list('pk', flat=True))
        after = {user.pk for user in form.cleaned_data['members']}
        with transaction.atomic():
            group.user_set.set(form.cleaned_data['members'])
            for user in User.objects.filter(pk__in=before ^ after):
                added = user.pk in after
                notify(user, Notification.Kind.SYSTEM, 'Vos rôles ont évolué',
                       f'Le rôle « {group.name} » vous a été {"attribué" if added else "retiré"} par un administrateur.')
            log_activity(request.user, ActivityLog.Verb.ROLE_CHANGED,
                         f'Membres du rôle « {group.name} » mis à jour ({len(after)} membre(s)).', team=None)
        messages.success(request, f'Membres du rôle « {group.name} » enregistrés.')
        return redirect('accounts:role_list')
    return render(request, 'accounts/admin/role_members.html', {'form': form, 'group': group})


@superuser_required
def role_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    role = Role.objects.filter(group=group).first()
    if (role and role.is_system) or group.name == settings.ECOTEAMS_DEFAULT_ROLE:
        messages.error(request, 'Le rôle par défaut ne peut pas être supprimé.')
        return redirect('accounts:role_list')
    if request.method == 'POST':
        name = group.name
        with transaction.atomic():
            group.delete()
            log_activity(request.user, ActivityLog.Verb.ROLE_CHANGED, f'Rôle « {name} » supprimé.', team=None)
        messages.success(request, f'Rôle « {name} » supprimé.')
        return redirect('accounts:role_list')
    return render(request, 'core/confirm_delete.html', {
        'object_label': f'le rôle « {group.name} »',
        'warning': f'{group.user_set.count()} utilisateur(s) perdront les permissions associées à ce rôle.',
        'cancel_url': reverse('accounts:role_list'),
    })


@superuser_required
def user_list(request):
    users = User.objects.annotate(points=Coalesce(Sum('point_transactions__amount'), 0)).prefetch_related('groups')
    query = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    status = request.GET.get('status', '')
    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query)
                             | Q(first_name__icontains=query) | Q(last_name__icontains=query))
    if role == 'admin':
        users = users.filter(is_superuser=True)
    elif role.isdigit():
        users = users.filter(groups__pk=int(role))
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)
    page = Paginator(users.order_by('-date_joined'), 20).get_page(request.GET.get('page'))
    memberships = {m.user_id: m for m in Membership.objects.filter(user__in=list(page)).select_related('team')}
    for user in page:
        user.membership = memberships.get(user.pk)
    return render(request, 'accounts/admin/user_list.html', {
        'page': page, 'query': query, 'role': role, 'status': status, 'groups': Group.objects.order_by('name'),
    })


@superuser_required
def user_edit(request, pk):
    target = get_object_or_404(User, pk=pk)
    if target.is_superuser:
        messages.info(request, 'Les comptes administrateurs se gèrent via la commande createsuperuser ou l’admin Django.')
        return redirect('accounts:user_list')
    form = UserAccessForm(request.POST or None, target=target)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            groups = set(form.cleaned_data['groups']) | {get_default_role_group()}
            target.groups.set(groups)
            target.is_active = form.cleaned_data['is_active']
            target.save(update_fields=['is_active'])
            log_activity(request.user, ActivityLog.Verb.ROLE_CHANGED,
                         f'Accès de {target.display_name} mis à jour.', team=None)
            notify(target, Notification.Kind.SYSTEM, 'Vos accès ont été mis à jour',
                   'Un administrateur a modifié vos rôles sur EcoTeams.')
        messages.success(request, f'Accès de {target.display_name} enregistrés.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/admin/user_edit.html', {
        'form': form, 'target': target, 'membership': get_membership(target), 'points': user_points(target),
    })
