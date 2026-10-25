/* EcoTeams — AI Goal Studio (vanilla JS).
   The AI answer is untrusted text: it is only ever inserted with textContent, never as HTML. */
(function () {
  'use strict';
  var root = document.getElementById('studio');
  if (!root) { return; }
  var form = document.getElementById('studio-form');
  var area = document.getElementById('ambition');
  var count = document.getElementById('ambition-count');
  var button = document.getElementById('studio-button');
  var label = document.getElementById('studio-button-label');
  var result = document.getElementById('studio-result');
  var max = parseInt(area.getAttribute('maxlength'), 10) || 400;
  var TONES = { facile: 'success', moyen: 'info', ambitieux: 'warning' };

  function csrfToken() {
    var field = form.querySelector('input[name=csrfmiddlewaretoken]');
    return field ? field.value : '';
  }

  function post(url, params) {
    var body = new URLSearchParams(params).toString();
    return fetch(url, {
      method: 'POST', credentials: 'same-origin',
      headers: { 'X-CSRFToken': csrfToken(), 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body
    }).then(function (response) {
      return response.json().then(function (data) { data.httpStatus = response.status; return data; });
    });
  }

  function node(tag, className, text) {
    var el = document.createElement(tag);
    if (className) { el.className = className; }
    if (text !== undefined) { el.textContent = text; }
    return el;
  }

  function clear() { while (result.firstChild) { result.removeChild(result.firstChild); } }

  function notice(text, kind) {
    clear();
    var box = node('div', 'alert alert-' + kind);
    box.appendChild(node('p', '', text));
    result.appendChild(box);
  }

  function setBusy(busy) {
    button.disabled = busy;
    button.setAttribute('aria-busy', busy ? 'true' : 'false');
    label.textContent = busy ? 'L’IA réfléchit…' : 'Générer 3 objectifs';
  }

  function formatDate(iso) {
    var parts = iso.split('-');
    return parts[2] + '/' + parts[1] + '/' + parts[0];
  }

  function card(item, data) {
    var article = node('article', 'card card-hover studio-card');
    var top = node('div', 'row');
    top.appendChild(node('span', 'pill tone-' + (TONES[item.difficulty] || 'muted'), item.difficulty));
    top.appendChild(node('span', 'pill tone-muted', item.tracking));
    article.appendChild(top);
    article.appendChild(node('h3', 'mt-1', item.title));
    article.appendChild(node('p', 'small text-2', item.why));
    var meta = node('p', 'small mt-1');
    meta.appendChild(node('strong', '', item.target + ' ' + item.unit));
    meta.appendChild(document.createTextNode(' · ' + item.category + ' · avant le ' + formatDate(item.deadline)));
    article.appendChild(meta);
    if (item.first_step) {
      var step = node('p', 'small mt-1');
      step.appendChild(node('strong', '', 'Premier pas : '));
      step.appendChild(document.createTextNode(item.first_step));
      article.appendChild(step);
    }
    var action = node('button', 'btn btn-primary btn-block mt-2', item.accepted ? 'Déjà créé' : 'Créer cet objectif');
    action.type = 'button';
    action.disabled = !!item.accepted;
    action.setAttribute('aria-label', 'Créer l’objectif « ' + item.title + ' »');
    action.addEventListener('click', function () { accept(action, item, data); });
    article.appendChild(action);
    return article;
  }

  function accept(action, item, data) {
    action.disabled = true;
    action.textContent = 'Création…';
    post(data.accept_url, { run: data.run_id, index: item.index }).then(function (reply) {
      if (reply.status === 'created') {
        action.textContent = 'Créé ✓';
        var link = node('a', 'btn btn-ghost btn-sm btn-block mt-1', 'Voir l’objectif');
        link.href = reply.url;
        action.parentNode.appendChild(link);
        link.focus();
      } else {
        action.disabled = false;
        action.textContent = 'Créer cet objectif';
        var alert = node('p', 'small text-danger mt-1', reply.error || 'Création impossible.');
        alert.setAttribute('role', 'alert');
        action.parentNode.appendChild(alert);
      }
    }).catch(function () {
      action.disabled = false;
      action.textContent = 'Créer cet objectif';
    });
  }

  function render(data) {
    clear();
    var grid = node('div', 'grid grid-3');
    data.proposals.forEach(function (item) { grid.appendChild(card(item, data)); });
    result.appendChild(grid);
    var seconds = (data.latency_ms / 1000).toFixed(1).replace('.', ',');
    result.appendChild(node('p', 'small text-2 mt-2',
      data.valid + ' proposition' + (data.valid > 1 ? 's' : '') + ' valide' + (data.valid > 1 ? 's' : '') +
      ' sur ' + data.total + ' · générées en ' + seconds + ' s · modèle ' + data.model));
  }

  function skeleton() {
    clear();
    var grid = node('div', 'grid grid-3');
    for (var i = 0; i < 3; i += 1) {
      var ghost = node('div', 'card studio-ghost');
      ghost.setAttribute('aria-hidden', 'true');
      ghost.appendChild(node('div', 'skeleton-line'));
      ghost.appendChild(node('div', 'skeleton-line short'));
      ghost.appendChild(node('div', 'skeleton-line'));
      grid.appendChild(ghost);
    }
    result.appendChild(grid);
    result.appendChild(node('p', 'sr-only', 'L’IA prépare vos objectifs…'));
  }

  function submit(event) {
    event.preventDefault();
    var text = area.value.trim();
    if (text.length < 8) {
      notice('Décrivez votre ambition en quelques mots (8 caractères minimum).', 'danger');
      area.focus();
      return;
    }
    setBusy(true);
    skeleton();
    post(root.getAttribute('data-propose-url'), { ambition: text }).then(function (data) {
      if (data.status === 'done') { render(data); } else { notice(data.error || 'Génération impossible.', 'danger'); }
    }).catch(function () {
      notice('Impossible de contacter le serveur. Réessayez.', 'danger');
    }).then(function () { setBusy(false); });
  }

  function updateCount() { count.textContent = area.value.length + ' / ' + max; }

  form.addEventListener('submit', submit);
  area.addEventListener('input', updateCount);
  Array.prototype.forEach.call(document.querySelectorAll('[data-example]'), function (chip) {
    chip.addEventListener('click', function () {
      area.value = chip.getAttribute('data-example');
      updateCount();
      area.focus();
    });
  });
  updateCount();
})();
