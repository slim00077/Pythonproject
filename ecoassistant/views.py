from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import AssistantError, ask


@login_required
def chat(request):
    history = request.session.get('ecoassistant_history', [])
    error = None
    question = ''
    if request.method == 'POST':
        if request.POST.get('clear'):
            request.session.pop('ecoassistant_history', None)
            return render(request, 'ecoassistant/chat.html', {'history': [], 'question': ''})
        question = request.POST.get('question', '')
        try:
            answer, recommendations = ask(request.user, question, history)
            history.extend([
                {'role': 'user', 'content': question},
                {'role': 'assistant', 'content': answer,
                 'recommendations': [{'name': a.name, 'points': a.points, 'slug': a.slug} for a in recommendations]},
            ])
            request.session['ecoassistant_history'] = history[-10:]
        except AssistantError as exc:
            error = str(exc)
    return render(request, 'ecoassistant/chat.html', {
        'history': history, 'error': error, 'question': question,
    })

