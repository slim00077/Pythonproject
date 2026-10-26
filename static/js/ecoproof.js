/* EcoProof AI — progressive enhancement of the Défis page.
   Analysis is a JSON call to the server (the API key never reaches the browser); everything returned is rendered with
   textContent only. Submitting is a plain POST of the same form, so it works without this script. */
(function () {
  'use strict';

  var panel = document.getElementById('ecoproof-panel');
  var toggle = document.getElementById('ecoproof-toggle');
  var form = document.getElementById('ecoproof-form');
  if (!panel || !toggle || !form) { return; }

  var analyzeButton = document.getElementById('ecoproof-analyze');
  var loading = document.getElementById('ecoproof-loading');
  var errorBox = document.getElementById('ecoproof-error');
  var errorText = document.getElementById('ecoproof-error-text');
  var results = document.getElementById('ecoproof-results');
  var TIMEOUT_MS = 90000;

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text) { node.textContent = text; }
    return node;
  }

  toggle.addEventListener('click', function () {
    var open = panel.hidden;
    panel.hidden = !open;
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggle.querySelector('[data-label]').textContent = open ? 'Réduire EcoProof AI' : 'Ouvrir EcoProof AI';
    if (open) { form.querySelector('textarea, select, input').focus(); }
  });

  function showError(message) {
    errorText.textContent = message;
    errorBox.hidden = false;
  }

  function card(title, icon) {
    var node = el('article', 'ecoproof-card');
    node.appendChild(el('h3', '', title));
    if (icon) { node.dataset.tone = icon; }
    return node;
  }

  function bullets(items, className) {
    var list = el('ul', className || 'ep-list small');
    items.forEach(function (item) { list.appendChild(el('li', '', item)); });
    return list;
  }

  function field(name) { return form.elements[name]; }

  function render(data) {
    results.textContent = '';
    var ai = data.ai;

    if (!data.ai_used) {
      var banner = el('div', 'alert ' + (data.ai_error ? 'alert-warning' : 'alert-info'));
      banner.setAttribute('role', 'note');
      banner.appendChild(el('p', 'mb-0', data.ai_error || data.notice));
      results.appendChild(banner);
    } else if (data.image_note) {
      var note = el('div', 'alert alert-warning');
      note.appendChild(el('p', 'mb-0', data.image_note));
      results.appendChild(note);
    }

    var grid = el('div', 'ecoproof-grid');

    var checks = card(data.ai_used ? 'Vérifications de complétude' : 'Vérifications de base (sans IA)');
    var checkList = el('ul', 'ecoproof-checks');
    data.checks.forEach(function (check) {
      var li = el('li', check.ok ? 'ok' : 'todo');
      li.appendChild(el('span', 'mark', check.ok ? '✓' : '!'));
      li.appendChild(el('span', '', check.label));
      checkList.appendChild(li);
    });
    checks.appendChild(checkList);
    grid.appendChild(checks);

    if (ai) {
      var category = card('Catégorie suggérée', 'cyan');
      category.appendChild(el('p', 'ecoproof-big', ai.category_label || 'Non déterminée'));
      if (ai.suggested_action_name) {
        category.appendChild(el('p', 'small muted', 'Action du catalogue proposée : ' + ai.suggested_action_name));
        var select = field('action_type');
        if (select && !select.value && ai.suggested_action_type_id) {
          select.value = String(ai.suggested_action_type_id);
          category.appendChild(el('p', 'small', 'Sélectionnée pour vous dans le formulaire : vous pouvez la changer.'));
        }
      }
      grid.appendChild(category);

      if (ai.summary) {
        var summary = card('Résumé de l’action', 'blue');
        summary.appendChild(el('p', 'small', ai.summary));
        grid.appendChild(summary);
      }
      if (ai.missing_info.length || ai.questions.length) {
        var missing = card('Informations manquantes', 'amber');
        if (ai.missing_info.length) { missing.appendChild(bullets(ai.missing_info)); }
        if (ai.questions.length) {
          missing.appendChild(el('p', 'small muted', 'Questions à vous poser :'));
          missing.appendChild(bullets(ai.questions));
        }
        grid.appendChild(missing);
      }
      if (ai.suggested_evidence.length) {
        var evidence = card('Preuves complémentaires suggérées', 'violet');
        evidence.appendChild(bullets(ai.suggested_evidence));
        grid.appendChild(evidence);
      }
      if (ai.image_observations) {
        var photo = card('Ce que l’IA voit sur la photo', 'violet');
        photo.appendChild(el('p', 'small', ai.image_observations));
        photo.appendChild(el('p', 'small muted', 'Une description automatique ne prouve pas l’authenticité de la photo.'));
        grid.appendChild(photo);
      }
    }

    var environment = card('Estimation environnementale', 'emerald');
    if (data.estimate) {
      environment.appendChild(el('p', 'ecoproof-big', '≈ ' + data.estimate.kg + ' kg CO₂e'));
      environment.appendChild(el('p', 'small muted', 'Calcul : quantité × ' + data.estimate.factor + ' kg CO₂e' +
        (data.estimate.unit ? ' par ' + data.estimate.unit : '') + ' (action « ' + data.estimate.action + ' »). Source du facteur : ' +
        data.estimate.source + '. Estimation indicative, non vérifiée.'));
    } else {
      environment.appendChild(el('p', 'small muted',
        'Aucune estimation chiffrée : elle exige une action du catalogue avec un facteur documenté et une quantité.'));
    }
    if (ai && ai.expected_benefit) { environment.appendChild(el('p', 'small', ai.expected_benefit)); }
    grid.appendChild(environment);

    var flags = (data.duplicates || []).concat(ai ? ai.moderator_points : []);
    if (flags.length) {
      var moderator = card('Points à vérifier par le modérateur', 'amber');
      moderator.appendChild(bullets(flags));
      grid.appendChild(moderator);
    }
    results.appendChild(grid);

    if (ai && ai.draft_description) {
      var draft = el('div', 'ecoproof-draft');
      draft.appendChild(el('h3', '', 'Description reformulée (brouillon à relire)'));
      draft.appendChild(el('p', 'small', ai.draft_description));
      var apply = el('button', 'btn btn-ghost btn-sm', 'Remplacer ma description par ce brouillon');
      apply.type = 'button';
      apply.addEventListener('click', function () {
        field('description').value = ai.draft_description;
        apply.disabled = true;
        apply.textContent = 'Brouillon appliqué — relisez-le avant l’envoi';
      });
      draft.appendChild(apply);
      results.appendChild(draft);
    }

    var footer = data.ai_used
      ? 'Analyse IA (' + data.model + ') réalisée en ' + data.elapsed + ' s. '
      : '';
    results.appendChild(el('p', 'small muted', footer + data.disclaimer));
    results.hidden = false;
  }

  var running = false;

  // The loader is always cleared in `finally`: success, server error, network failure, timeout or a bug in render().
  analyzeButton.addEventListener('click', async function () {
    if (running) { return; }
    errorBox.hidden = true;
    results.hidden = true;
    var description = field('description').value.trim();
    if (description.length < 10) {
      showError('Décrivez votre action en quelques mots (10 caractères minimum) avant de lancer l’analyse.');
      field('description').focus();
      return;
    }
    running = true;
    loading.hidden = false;
    analyzeButton.disabled = true;
    analyzeButton.classList.add('is-loading');
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, TIMEOUT_MS);
    try {
      var response = await fetch(panel.getAttribute('data-analyze-url'), {
        method: 'POST', credentials: 'same-origin', body: new FormData(form), signal: controller.signal,
        headers: { 'X-CSRFToken': panel.getAttribute('data-csrf'), 'Accept': 'application/json' },
      });
      var data;
      try { data = await response.json(); } catch (parseError) { data = { ok: false, error: 'Réponse inattendue du serveur.' }; }
      if (data.ok) {
        render(data);
      } else {
        var details = data.errors ? Object.keys(data.errors).map(function (k) { return data.errors[k].join(' '); }).join(' ') : '';
        showError((data.error || 'L’analyse n’a pas pu aboutir.') + (details ? ' ' + details : ''));
      }
    } catch (error) {
      showError(error && error.name === 'AbortError'
        ? 'L’analyse a pris trop de temps. Réessayez, ou soumettez votre déclaration sans analyse.'
        : 'Impossible de joindre le serveur. Vos informations sont conservées : réessayez ou soumettez votre déclaration.');
    } finally {
      clearTimeout(timer);
      loading.hidden = true;
      analyzeButton.disabled = false;
      analyzeButton.classList.remove('is-loading');
      running = false;
    }
  });
}());
