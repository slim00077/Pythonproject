/* EcoPulse — progressive AI panel (dashboard). Mission buttons are plain POST forms and need no script.
   The AI output is rendered with textContent only, never as HTML. */
(function () {
  'use strict';

  var panel = document.getElementById('ep-ai');
  if (!panel) { return; }
  var runButton = document.getElementById('ep-ai-run');
  var loading = document.getElementById('ep-ai-loading');
  var errorBox = document.getElementById('ep-ai-error');
  var errorText = document.getElementById('ep-ai-error-text');
  var result = document.getElementById('ep-ai-result');
  if (!runButton || !loading || !errorBox || !errorText || !result) { return; }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text) { node.textContent = text; }
    return node;
  }

  function postForm(url, body) {
    return fetch(url, {
      method: 'POST', credentials: 'same-origin',
      headers: { 'X-CSRFToken': panel.getAttribute('data-csrf'), 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body,
    }).then(function (response) {
      return response.json().catch(function () { return { ok: false, error: 'Réponse inattendue du serveur.' }; });
    });
  }

  function hidden(name, value) {
    var input = document.createElement('input');
    input.type = 'hidden'; input.name = name; input.value = value;
    return input;
  }

  // A real POST form (CSRF token, then a server redirect), identical to the server-rendered mission cards.
  function saveForm(batch, index, mode, label, css) {
    var form = el('form', 'inline-form');
    form.method = 'post';
    form.action = panel.getAttribute('data-save-url');
    form.appendChild(hidden('csrfmiddlewaretoken', panel.getAttribute('data-csrf')));
    form.appendChild(hidden('batch', batch));
    form.appendChild(hidden('index', index));
    form.appendChild(hidden('mode', mode));
    var button = el('button', css, label);
    button.type = 'submit';
    form.appendChild(button);
    return form;
  }

  function renderProposal(batch, proposal, index) {
    var card = el('div', 'ep-proposal');
    var head = el('div', 'row between');
    head.appendChild(el('strong', '', proposal.title));
    head.appendChild(el('span', 'pill ' + (proposal.setting === 'indoor' ? 'tone-violet' : 'tone-blue'),
      proposal.setting === 'indoor' ? 'Intérieur' : 'Extérieur'));
    card.appendChild(head);
    card.appendChild(el('p', 'small', proposal.description));
    var steps = el('ol', 'ep-list small');
    proposal.instructions.forEach(function (step) { steps.appendChild(el('li', '', step)); });
    card.appendChild(steps);
    var actions = el('div', 'row');
    actions.appendChild(saveForm(batch, index, 'draft', 'Brouillon', 'btn btn-secondary btn-sm'));
    actions.appendChild(saveForm(batch, index, 'pending', 'Soumettre à validation', 'btn btn-primary btn-sm'));
    card.appendChild(actions);
    return card;
  }

  function render(data) {
    result.textContent = '';
    if (data.basis) { result.appendChild(el('p', 'small muted', 'Basée sur : ' + data.basis)); }
    result.appendChild(el('h3', 'ep-sub', 'Explication des mesures (générée par IA)'));
    result.appendChild(el('p', '', data.summary));
    if (data.recommendations.length) {
      result.appendChild(el('h3', 'ep-sub', 'Actions recommandées'));
      var list = el('ul', 'ep-list');
      data.recommendations.forEach(function (item) {
        var li = el('li');
        li.appendChild(el('strong', '', item.title + ' '));
        li.appendChild(el('span', 'pill ' + (item.setting === 'indoor' ? 'tone-violet' : 'tone-blue'),
          item.setting === 'indoor' ? 'intérieur' : 'extérieur'));
        if (item.detail) { li.appendChild(el('div', 'small muted', item.detail)); }
        list.appendChild(li);
      });
      result.appendChild(list);
    }
    if (data.event_advice) {
      var alertBox = el('div', 'alert alert-warning');
      alertBox.appendChild(el('p', 'mb-0', data.event_advice));
      result.appendChild(alertBox);
    }
    if (data.proposals.length) {
      result.appendChild(el('h3', 'ep-sub', 'Missions proposées par l’IA (à relire)'));
      data.proposals.forEach(function (proposal, index) {
        result.appendChild(renderProposal(data.batch_id, proposal, index));
      });
    }
    if (data.limitations) { result.appendChild(el('p', 'small muted', 'Limites : ' + data.limitations)); }
    result.appendChild(el('p', 'small muted', 'Modèle ' + data.model + ' · ' +
      (data.from_cache ? 'résultat en cache' : 'généré en ' + data.elapsed + ' s') + ' · Les valeurs mesurées et leur classement viennent des règles, pas de l’IA.'));
    result.hidden = false;
  }

  var TIMEOUT_MS = 75000;
  var running = false;

  function showError(message) {
    errorText.textContent = message;
    errorBox.hidden = false;
  }

  // The loader is always cleared in `finally`: success, server error, network failure, timeout or a bug in render().
  runButton.addEventListener('click', async function () {
    if (running) { return; }
    running = true;
    errorBox.hidden = true; result.hidden = true; loading.hidden = false;
    runButton.disabled = true; runButton.classList.add('is-loading');
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, TIMEOUT_MS);
    try {
      var response = await fetch(panel.getAttribute('data-url'), {
        method: 'POST', credentials: 'same-origin', signal: controller.signal,
        headers: { 'X-CSRFToken': panel.getAttribute('data-csrf'), 'Accept': 'application/json' },
      });
      var data;
      try { data = await response.json(); } catch (parseError) { data = { ok: false, error: 'Réponse inattendue du serveur.' }; }
      if (data.ok) {
        render(data);
      } else {
        showError(data.error || 'L’analyse n’a pas pu aboutir. Réessayez dans un instant.');
      }
    } catch (error) {
      showError(error && error.name === 'AbortError'
        ? 'L’analyse a pris trop de temps. Réessayez dans un instant ; les recommandations par règles restent disponibles.'
        : 'Impossible de joindre le serveur. Vérifiez votre connexion puis réessayez.');
    } finally {
      clearTimeout(timer);
      loading.hidden = true;
      runButton.disabled = false; runButton.classList.remove('is-loading');
      running = false;
    }
  });
}());
