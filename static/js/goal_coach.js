/* EcoTeams — AI goal coach (progressive enhancement, vanilla JS).
   POSTs a request, then polls the status endpoint until the background call finishes. */
(function () {
  'use strict';
  var root = document.getElementById('coach');
  if (!root) { return; }
  var button = document.getElementById('coach-button');
  var label = document.getElementById('coach-button-label');
  var result = document.getElementById('coach-result');
  var rating = document.getElementById('coach-rating');
  var POLL_MS = 1500;
  var MAX_POLLS = 60;

  function csrfToken() {
    var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    if (match) { return decodeURIComponent(match[1]); }
    var field = document.querySelector('input[name=csrfmiddlewaretoken]');
    return field ? field.value : '';
  }

  function post(url, body) {
    return fetch(url, {
      method: 'POST', credentials: 'same-origin',
      headers: { 'X-CSRFToken': csrfToken(), 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body || ''
    }).then(function (response) {
      return response.json().then(function (data) { data.httpStatus = response.status; return data; });
    });
  }

  function show(node) { result.textContent = ''; result.appendChild(node); }

  function message(text, kind) {
    var box = document.createElement('div');
    box.className = 'alert alert-' + kind;
    var p = document.createElement('p');
    p.textContent = text;
    box.appendChild(p);
    return box;
  }

  function setBusy(busy) {
    button.disabled = busy;
    button.setAttribute('aria-busy', busy ? 'true' : 'false');
    label.textContent = busy ? 'Analyse en cours…' : 'Obtenir un nouveau conseil';
  }

  function render(data) {
    if (data.status === 'done') {
      var text = document.createElement('div');
      text.className = 'prose coach-text';
      text.id = 'coach-text';
      text.style.whiteSpace = 'pre-line';
      text.textContent = data.content;
      show(text);
      rating.hidden = false;
      rating.setAttribute('data-rate-url', data.rate_url);
      rating.querySelectorAll('[data-helpful]').forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
      setBusy(false);
    } else if (data.status === 'failed' || data.status === 'refused') {
      show(message(data.error || 'Le conseil n’a pas pu être généré.', 'danger'));
      rating.hidden = true;
      setBusy(false);
    }
  }

  function poll(url, count) {
    if (count > MAX_POLLS) {
      show(message('Le coach met trop de temps à répondre. Réessayez dans un instant.', 'danger'));
      setBusy(false);
      return;
    }
    window.setTimeout(function () {
      fetch(url, { credentials: 'same-origin' }).then(function (r) { return r.json(); }).then(function (data) {
        if (data.status === 'pending') { poll(url, count + 1); } else { render(data); }
      }).catch(function () {
        show(message('Connexion perdue. Rechargez la page pour voir le conseil.', 'danger'));
        setBusy(false);
      });
    }, POLL_MS);
  }

  function start() {
    setBusy(true);
    rating.hidden = true;
    show(message('Le coach analyse vos progrès…', 'info'));
    post(root.getAttribute('data-request-url')).then(function (data) {
      if (data.status === 'pending') { poll(data.status_url, 0); } else { render(data); }
    }).catch(function () {
      show(message('Impossible de contacter le serveur.', 'danger'));
      setBusy(false);
    });
  }

  button.addEventListener('click', start);

  rating.addEventListener('click', function (event) {
    var target = event.target.closest('[data-helpful]');
    if (!target) { return; }
    post(rating.getAttribute('data-rate-url'), 'helpful=' + target.getAttribute('data-helpful')).then(function (data) {
      if (data.error) { return; }
      rating.querySelectorAll('[data-helpful]').forEach(function (b) {
        b.setAttribute('aria-pressed', b === target ? 'true' : 'false');
      });
    });
  });

  if (root.getAttribute('data-status-url')) {
    setBusy(true);
    show(message('Le coach analyse vos progrès…', 'info'
