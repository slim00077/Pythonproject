from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from challenges.models import Challenge
from core.choices import EcoCategory
from core.decorators import any_permission_required
from core.exceptions import BusinessRuleError
from core.permissions import MANAGE_ACTION_TYPES, MODERATE_ACTIONS

from . import services
from .forms import ActionTypeForm, CatalogFilterForm, ModerationForm, SubmissionForm
from .models import ActionSubmission, EcoActionType


@login_required
def submission_list(request):
    assistant_history = request.session.get('ecoassistant_history', [])
    assistant_error = None
    if request.method == 'POST' and 'assistant_question' in request.POST:
        from ecoassistant.services import AssistantError, ask

        question = request.POST.get('assistant_question', '').strip()
        if request.POST.get('clear_assistant'):
            request.session.pop('ecoassistant_history', None)
            assistant_history = []
        else:
            try:
                answer, recommendations = ask(request.user, question, assistant_history)
                assistant_history.extend([
                    {'role': 'user', 'content': question},
                    {'role': 'assistant', 'content': answer,
                     'recommendations': [
                         {'name': action.name, 'points': action.points, 'slug': action.slug}
                         for action in recommendations
                     ]},
                ])
                request.session['ecoassistant_history'] = assistant_history[-10:]
            except AssistantError as error:
                assistant_error = str(error)
    status = request.GET.get('status', '')
    submissions = ActionSubmission.objects.filter(user=request.user).select_related('action_type', 'challenge')
    counts = dict(submissions.order_by().values_list('status').annotate(total=Count('pk')))
    if status in ActionSubmission.Status.values:
        submissions = submissions.filter(status=status)
    totals = ActionSubmission.objects.filter(user=request.user, status=ActionSubmission.Status.APPROVED).aggregate(
        points=Coalesce(Sum('points_awarded'), 0), co2=Sum('co2_saved_kg'),
    )
    page = Paginator(submissions, 10).get_page(request.GET.get('page'))
    return render(request, 'actions/submission_list.html', {
        'page': page, 'status': status, 'counts': counts, 'totals': totals,
        'statuses': ActionSubmission.Status.choices,
        'assistant_history': assistant_history,
        'assistant_error': assistant_error,
    })


@login_required
def catalog(request):
    form = CatalogFilterForm(request.GET or None)
    action_types = EcoActionType.objects.filter(is_active=True).annotate(
        approved_total=Count('submissions', filter=Q(submissions__status='approved'))
    )
    if form.is_valid():
        if form.cleaned_data['q']:
            action_types = action_types.filter(
                Q(name__icontains=form.cleaned_data['q']) | Q(description__icontains=form.cleaned_data['q']))
        if form.cleaned_data['category']:
            action_types = action_types.filter(category=form.cleaned_data['category'])
    return render(request, 'actions/catalog.html', {'form': form, 'action_types': action_types})


@login_required
def submission_create(request):
    initial = {}
    action_type = EcoActionType.objects.filter(slug=request.GET.get('type', ''), is_active=True).first()
    if action_type:
        initial['action_type'] = action_type
    challenge = Challenge.objects.filter(slug=request.GET.get('challenge', '')).first()
    if challenge:
        initial['challenge'] = challenge
    form = SubmissionForm(request.POST or None, request.FILES or None, user=request.user, initial=initial)
    if request.method == 'POST' and form.is_valid():
        submission = services.create_submission(request.user, form)
        messages.success(request, 'Action déclarée ! Elle sera examinée par la modération avant l’attribution des points.')
        return redirect(submission)
    return render(request, 'actions/submission_form.html', {
        'form': form, 'is_create': True,
        'action_types': EcoActionType.objects.filter(is_active=True),
    })


def _own_submission(request, pk):
    return get_object_or_404(ActionSubmission.objects.select_related('action_type'), pk=pk, user=request.user)


@login_required
def submission_detail(request, pk):
    submission = get_object_or_404(
        ActionSubmission.objects.select_related('action_type', 'challenge', 'team', 'reviewed_by', 'user'), pk=pk
    )
    if not services.can_view_submission(request.user, submission):
        raise Http404
    return render(request, 'actions/submission_detail.html', {
        'submission': submission,
        'logs': submission.moderation_logs.select_related('moderator'),
        'is_owner': submission.user_id == request.user.pk,
    })


@login_required
def submission_update(request, pk):
    submission = _own_submission(request, pk)
    if not submission.is_editable:
        messages.error(request, 'Une déclaration déjà modérée ne peut plus être modifiée.')
        return redirect(submission)
    form = SubmissionForm(request.POST or None, request.FILES or None, instance=submission, user=request.user)
    if request.method == 'POST' and form.is_valid():
        services.update_submission(request.user, submission, form)
        messages.success(request, 'Déclaration mise à jour.')
        return redirect(submission)
    return render(request, 'actions/submission_form.html', {
        'form': form, 'submission': submission, 'is_create': False,
        'action_types': EcoActionType.objects.filter(is_active=True),
    })


@login_required
def submission_delete(request, pk):
    submission = _own_submission(request, pk)
    if not submission.is_editable:
        messages.error(request, 'Une déclaration déjà modérée ne peut pas être supprimée.')
        return redirect(submission)
    if request.method == 'POST':
        services.delete_submission(request.user, submission)
        messages.success(request, 'Déclaration supprimée.')
        return redirect('actions:list')
    return render(request, 'core/confirm_delete.html', {
        'object_label': f'la déclaration « {submission.action_type.name} » du {submission.performed_on:%d/%m/%Y}',
        'warning': 'Cette déclaration en attente sera définitivement supprimée.',
        'cancel_url': submission.get_absolute_url(),
    })


@login_required
def evidence(request, pk):
    """Serve an evidence photo only to its author and to moderators."""
    submission = get_object_or_404(ActionSubmission, pk=pk)
    if not submission.evidence or not services.can_view_submission(request.user, submission):
        raise Http404
    try:
        handle = submission.evidence.open('rb')
    except FileNotFoundError:
        raise Http404
    return FileResponse(handle)


# --- Back-office: moderation --------------------------------------------------

@any_permission_required(MODERATE_ACTIONS)
def moderation_list(request):
    tab = request.GET.get('tab', 'pending')
    if tab not in ActionSubmission.Status.values:
        tab = 'pending'
    submissions = ActionSubmission.objects.filter(status=tab).select_related('user', 'action_type', 'challenge')
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    if query:
        submissions = submissions.filter(
            Q(user__username__icontains=query) | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query) | Q(description__icontains=query))
    if category:
        submissions = submissions.filter(action_type__category=category)
    submissions = submissions.order_by('created_at' if tab == 'pending' else '-reviewed_at')
    counts = dict(ActionSubmission.objects.order_by().values_list('status').annotate(total=Count('pk')))
    page = Paginator(submissions, 15).get_page(request.GET.get('page'))
    return render(request, 'actions/admin/moderation_list.html', {
        'page': page, 'tab': tab, 'counts': counts, 'query': query, 'category': category,
        'categories': EcoCategory.choices, 'statuses': ActionSubmission.Status.choices,
    })


@any_permission_required(MODERATE_ACTIONS)
def moderation_detail(request, pk):
    submission = get_object_or_404(
        ActionSubmission.objects.select_related('user', 'action_type', 'challenge', 'team', 'reviewed_by'), pk=pk
    )
    form = ModerationForm(request.POST or None)
    ai_report = None
    if request.method == 'POST' and form.is_valid():
        decision = request.POST.get('decision')
        notes = form.cleaned_data['notes']
        try:
            if decision == 'ai_validate':
                ai_report = services.ai_validate_submission(submission)
                messages.info(request, 'Rapport IA généré. La décision finale reste celle du modérateur.')
            elif decision == 'approve':
                services.approve_submission(request.user, submission, notes)
                messages.success(request, f'Action validée : {submission.action_type.points} points attribués.')
            elif decision == 'reject':
                services.reject_submission(request.user, submission, notes)
                messages.success(request, 'Déclaration refusée. L’auteur a été notifié.')
            elif decision == 'revoke':
                services.revoke_approval(request.user, submission, notes)
                messages.success(request, 'Validation annulée et points retirés via une écriture de correction.')
            else:
                raise BusinessRuleError('Décision inconnue.')
        except BusinessRuleError as error:
            messages.error(request, error.message)
            if decision == 'ai_validate':
                ai_report = {'error': error.message}
            else:
                return redirect('actions_admin:moderation_detail', pk=submission.pk)
        if decision == 'ai_validate':
            pass
        else:
            next_pending = ActionSubmission.objects.filter(status=ActionSubmission.Status.PENDING).exclude(
                user=request.user).order_by('created_at').first()
            if next_pending and decision != 'revoke':
                return redirect('actions_admin:moderation_detail', pk=next_pending.pk)
            return redirect('actions_admin:moderation_list')
    history = ActionSubmission.objects.filter(user=submission.user).exclude(pk=submission.pk).select_related(
        'action_type')[:6]
    same_day = ActionSubmission.objects.filter(user=submission.user, performed_on=submission.performed_on).exclude(
        pk=submission.pk).count()
    return render(request, 'actions/admin/moderation_detail.html', {
        'submission': submission, 'form': form, 'history': history, 'same_day': same_day,
        'logs': submission.moderation_logs.select_related('moderator'),
        'estimate': submission.action_type.estimate_co2(submission.quantity),
        'is_own': submission.user_id == request.user.pk,
        'ai_report': ai_report,
    })


# --- Back-office: action catalogue -------------------------------------------

@any_permission_required(MANAGE_ACTION_TYPES)
def type_list(request):
    action_types = EcoActionType.objects.annotate(submission_total=Count('submissions')).order_by('category', 'name')
    return render(request, 'actions/admin/type_list.html', {'action_types': action_types})


@any_permission_required(MANAGE_ACTION_TYPES)
def type_form(request, pk=None):
    action_type = get_object_or_404(EcoActionType, pk=pk) if pk else None
    form = ActionTypeForm(request.POST or None, instance=action_type)
    if request.method == 'POST' and form.is_valid():
        saved = form.save()
        messages.success(request, f'Action « {saved.name} » enregistrée.')
        return redirect('actions_admin:type_list')
    return render(request, 'actions/admin/type_form.html', {'form': form, 'action_type': action_type})


@any_permission_required(MANAGE_ACTION_TYPES)
@require_POST
def type_toggle(request, pk):
    action_type = get_object_or_404(EcoActionType, pk=pk)
    action_type.is_active = not action_type.is_active
    action_type.save(update_fields=['is_active', 'updated_at'])
    state = 'activée' if action_type.is_active else 'désactivée'
    messages.success(request, f'Action « {action_type.name} » {state}.')
    return redirect('actions_admin:type_list')
