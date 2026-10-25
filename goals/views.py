from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.exceptions import BusinessRuleError

from . import services
from .forms import GoalForm, ProgressForm
from .models import Goal


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
