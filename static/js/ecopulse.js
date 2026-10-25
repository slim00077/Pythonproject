/* EcoPulse — progressive AI panel. Renders with textContent only (the AI output is never injected as HTML). */
(function () {
  'use strict';

  var root = document.getElementById('ep-ai');
  if (!root) { return; }
  var runButton = document.getElementById('ep-ai-run');
  var loading = document.getElementById('ep-ai-loading');
  var errorBox = document.getElementById('ep-ai-error');
  var errorText = document.getElementById('ep-ai-error-text');
  var result = document.getElementById('ep-ai-result');
  if (!runButton) { return; }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text) { node.textContent = text; }
    return node;
  }

  function showError(message) {
    errorText.textContent = message;
    errorBox.hidden = false;
  }

  function postJson(url, body) {
    return fetch(url, {
      method: 'POST', credentials: 'same-origin',
      headers: { 'X-CSRFToken': root.getAttribute('data-csrf'), 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body,
    }).then(function (response) {
      return response.json().catch(function () { return { ok: false, error: 'Réponse inattendue du serveur.' }; });
    });
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
    card.appendChild(el('p', 'small muted', proposal.duration_days + ' j · ' + proposal.required_actions + ' action(s) requise(s)'));
    var actions = el('div', 'row');
    var status = el('span', 'small muted');
    [['draft', 'Enregistrer comme brouillon', 'btn btn-secondary btn-sm'],
     ['pending', 'Soumettre à validation', 'btn btn-primary btn-sm']].forEach(function (spec) {
      var button = el('button', spec[2], spec[1]);
      button.type = 'button';
      button.addEventListener('click', function () {
        actions.querySelectorAll('button').forEach(function (b) { b.disabled = true; });
        status.textContent = 'Enregistrement…';
        postJson(root.getAttribute('data-save-url'),
          'batch=' + encodeURIComponent(batch) + '&index=' + index + '&mode=' + spec[0])
          .then(function (data) {
            if (data.ok) {
              status.textContent = '';
              var link = el('a', '', data.message + ' Voir le défi');
              link.href = data.url;
              status.appendChild(link);
            } else {
              status.textContent = data.error || 'Échec de l’enregistrement.';
              actions.querySelectorAll('button').forEach(function (b) { b.disabled = false; });
            }
          })
          .catch(function () {
            status.textContent = 'Erreur réseau.';
            actions.querySelectorAll('button').forEach(function (b) { b.disabled = false; });
          });
      });
      actions.appendChild(button);
    });
    actions.appendChild(status);
    card.appendChild(actions);
    return card;
  }

  function render(data) {
    result.textContent = '';
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
      result.appendChild(el('h3', 'ep-sub', 'Missions proposées (à relire)'));
      data.proposals.forEach(function (proposal, index) {
        result.appendChild(renderProposal(data.batch_id, proposal, index));
      });
    } else {
      result.appendChild(el('p', 'small muted', 'Aucune mission n’a pu être proposée pour ces conditions.'));
    }
    if (data.limitations) { result.appendChild(el('p', 'small muted', 'Limites : ' + data.limitations)); }
    result.appendChild(el('p', 'small muted', 'Modèle ' + data.model + ' · ' +
      (data.from_cache ? 'résultat en cache' : 'généré en ' + data.elapsed + ' s')));
    result.hidden = false;
  }

  runButton.addEventListener('click', function () {
    errorBox.hidden = true;
    result.hidden = true;
    loading.hidden = false;
    runButton.disabled = true;
    runButton.classList.add('is-loading');
    postJson(root.getAttribute('data-url'), '')
      .then(function (data) { if (data.ok) { render(data); } else { showError(data.error || 'Analyse impossible.'); } })
      .catch(function () { showError('Erreur réseau : impossible de joindre le serveur.'); })
      .then(function () {
        loading.hidden = true;
        runButton.disabled = false;
        runButton.classList.remove('is-loading');
      });
  });
}());
