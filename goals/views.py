from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.exceptions import BusinessRuleError

from . import services, studio
from .forms import GoalForm, ProgressForm
from .models import Goal, GoalAdvice


def _own_goal(request, pk):
    return get_object_or_404(Goal, pk=pk, user=request.user)


@login_required
def goal_list(request):
    status = request.GET.get('status', 'active')
    goals = Goal.objects.filter(user=request.user)
    counts = dict(goals.order_by().values_list('status').annotate(total=Count('pk')))
    if status in Goal.Status.values:
        goals = goals.filter(status=status)
    goals = list(goals.order_by('deadline'))
    return render(request, 'goals/goal_list.html', {
        'goals': goals, 'status': status, 'counts': counts, 'statuses': Goal.Status.choices,
        'total': sum(counts.values()),
    })


@login_required
def goal_create(request):
    form = GoalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        goal = services.save_goal(request.user, form)
        messages.success(request, 'Objectif créé. À vous de jouer !')
        return redirect(goal)
    return render(request, 'goals/goal_form.html', {'form': form, 'is_create': True})


@login_required
def goal_detail(request, pk):
    goal = _own_goal(request, pk)
    return render(request, 'goals/goal_detail.html', {
        'goal': goal, 'progress_form': ProgressForm(initial={'value': goal.current_progress}),
        'advice': goal.advices.first(), 'ai_enabled': settings.ECOTEAMS_AI_ENABLED,
    })


@login_required
def goal_update(request, pk):
    goal = _own_goal(request, pk)
    form = GoalForm(request.POST or None, instance=goal)
    if request.method == 'POST' and form.is_valid():
        services.save_goal(request.user, form)
        messages.success(request, 'Objectif mis à jour.')
        return redirect(goal)
    return render(request, 'goals/goal_form.html', {'form': form, 'goal': goal, 'is_create': False})


@login_required
def goal_delete(request, pk):
    goal = _own_goal(request, pk)
    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Objectif supprimé.')
        return redirect('goals:list')
    return render(request, 'core/confirm_delete.html', {
        'object_label': f'l’objectif « {goal.title} »',
        'warning': 'Votre historique de points et vos badges ne sont pas affectés.',
        'cancel_url': goal.get_absolute_url(),
    })


@login_required
@require_POST
def goal_progress(request, pk):
    goal = _own_goal(request, pk)
    form = ProgressForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Indiquez une valeur positive.')
        return redirect(goal)
    try:
        goal = services.update_manual_progress(request.user, goal, form.cleaned_data['value'])
    except BusinessRuleError as error:
        messages.error(request, error.message)
    else:
        if goal.status == Goal.Status.COMPLETED:
            messages.success(request, 'Objectif atteint, félicitations !')
        else:
            messages.success(request, 'Progression enregistrée.')
    return redirect(goal)


@login_required
@require_POST
def goal_toggle(request, pk):
    goal = _own_goal(request, pk)
    abandon = goal.status != Goal.Status.ABANDONED
    try:
        services.set_abandoned(request.user, goal, abandon)
    except BusinessRuleError as error:
        messages.error(request, error.message)
    else:
        messages.success(request, 'Objectif mis en pause.' if abandon else 'Objectif réactivé.')
    return redirect(goal)


def _advice_payload(advice):
    return {
        'id': advice.pk, 'status': advice.status, 'content': advice.content, 'error': advice.error,
        'helpful': advice.helpful, 'latency_ms': advice.latency_ms,
        'rate_url': reverse('goals:advice_rate', args=[advice.goal_id, advice.pk]),
        'status_url': reverse('goals:advice_status', args=[advice.goal_id, advice.pk]),
    }


@login_required
@require_POST
def advice_request(request, pk):
    goal = _own_goal(request, pk)
    try:
        advice = services.request_advice(request.user, goal)
    except BusinessRuleError as error:
        return JsonResponse({'status': 'refused', 'error': error.message}, status=429 if 'Limite' in error.message else 409)
    return JsonResponse(_advice_payload(advice), status=202 if advice.status == GoalAdvice.Status.PENDING else 200)


@login_required
def advice_status(request, pk, advice_pk):
    advice = get_object_or_404(GoalAdvice, pk=advice_pk, goal_id=pk, user=request.user)
    return JsonResponse(_advice_payload(advice))


@login_required
@require_POST
def advice_rate(request, pk, advice_pk):
    advice = get_object_or_404(GoalAdvice, pk=advice_pk, goal_id=pk, user=request.user)
    value = request.POST.get('helpful')
    if value not in ('1', '0'):
        return JsonResponse({'error': 'Valeur invalide.'}, status=400)
    try:
        services.rate_advice(request.user, advice, value == '1')
    except BusinessRuleError as error:
        return JsonResponse({'error': error.message}, status=409)
    return JsonResponse(_advice_payload(advice))


# --- AI Goal Studio ---------------------------------------------------------

STUDIO_EXAMPLES = [
    'Je veux réduire ma consommation d’énergie à la maison avant la fin du trimestre',
    'Je voudrais me déplacer davantage à vélo et moins en voiture',
    'Je veux arrêter de gaspiller la nourriture',
    'Je veux mieux trier mes déchets et recycler plus',
]


def _proposal_payload(run):
    cards = []
    for index, proposal in enumerate(run.proposals):
        data = proposal['data']
        cards.append({
            'index': index, 'difficulty': proposal['difficulty'], 'title': data['title'], 'why': proposal['why'],
            'first_step': proposal['first_step'], 'category': dict(Goal._meta.get_field('category').choices).get(
                data['category'], 'Toutes catégories'),
            'tracking': Goal.TrackingMode(data['tracking_mode']).label, 'target': data['target_value'],
            'unit': data['unit'], 'deadline': data['deadline'], 'accepted': index in run.accepted,
        })
    return {
        'status': 'done', 'run_id': run.pk, 'proposals': cards, 'latency_ms': run.latency_ms,
        'valid': run.valid_count, 'total': run.total_count, 'model': run.model_name,
        'accept_url': reverse('goals:studio_accept'),
    }


@login_required
def goal_studio(request):
    history = studio.build_history(request.user)
    return render(request, 'goals/studio.html', {
        'history': history, 'examples': STUDIO_EXAMPLES, 'ai_enabled': settings.ECOTEAMS_AI_ENABLED,
        'max_length': studio.MAX_AMBITION,
    })


@login_required
@require_POST
def studio_propose(request):
    try:
        run = studio.propose(request.user, request.POST.get('ambition', ''))
    except BusinessRuleError as error:
        status = 429 if 'Limite' in error.message else 422
        return JsonResponse({'status': 'failed', 'error': error.message}, status=status)
    return JsonResponse(_proposal_payload(run))


@login_required
@require_POST
def studio_accept(request):
    try:
        run_id, index = int(request.POST.get('run', '')), int(request.POST.get('index', ''))
    except ValueError:
        return JsonResponse({'status': 'failed', 'error': 'Requête invalide.'}, status=400)
    try:
        goal = studio.accept(request.user, run_id, index)
    except BusinessRuleError as error:
        return JsonResponse({'status': 'failed', 'error': error.message}, status=409)
    return JsonResponse({'status': 'created', 'url': goal.get_absolute_url(), 'title': goal.title}, status=201)
