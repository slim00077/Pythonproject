(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var button = document.querySelector('[data-ai-generate]');
    var tagButton = document.querySelector('[data-suggest-tags]');
    if (!button && !tagButton) { return; }

    var form = (button || tagButton).form;
    var description = form.elements.namedItem('description');
    var csrf = form.querySelector('input[name="csrfmiddlewaretoken"]');

    function getFormValues() {
      return {
        title: form.elements.namedItem('title').value,
        description: description.value
      };
    }

    function requestJson(endpoint, values, button, status) {
      if (!csrf) {
        status.textContent = 'Jeton de sécurité manquant. Rechargez la page avant de réessayer.';
        return Promise.reject(new Error('Jeton CSRF manquant.'));
      }

      var body = new URLSearchParams();
      Object.keys(values).forEach(function (name) {
        body.set(name, values[name]);
      });
      if (button.getAttribute('data-event-slug')) {
        body.set('event_slug', button.getAttribute('data-event-slug'));
      }
      button.disabled = true;
      button.classList.add('is-loading');

      return fetch(endpoint, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
          'X-CSRFToken': csrf.value
        },
        body: body.toString()
      }).then(function (response) {
        return response.json().catch(function () {
          throw new Error(response.redirected ? 'Votre session a expiré. Reconnectez-vous.' : 'Réponse invalide du serveur.');
        }).then(function (data) {
          if (!response.ok) { throw new Error(data.error || 'La génération a échoué. Réessayez.'); }
          return data;
        });
      }).finally(function () {
        button.disabled = false;
        button.classList.remove('is-loading');
      });
    }

    if (button) {
      var status = document.querySelector('[data-ai-status]');
      button.addEventListener('click', function () {
        if (description.value.trim() && !window.confirm('Remplacer la description actuelle par une nouvelle proposition ?')) {
          return;
        }
        var values = getFormValues();
        ['category', 'start_at', 'location'].forEach(function (name) {
          values[name] = form.elements.namedItem(name).value;
        });
        status.textContent = 'Génération en cours…';
        requestJson(button.getAttribute('data-endpoint'), values, button, status).then(function (data) {
        description.value = data.description + '\n\nProgramme :\n' +
          data.program.map(function (item) { return '- ' + item; }).join('\n') +
          '\n\nHashtags : ' + data.hashtags.join(' ');
        description.dispatchEvent(new Event('input', { bubbles: true }));
        status.textContent = data.provider === 'template'
          ? 'Proposition générée avec les modèles locaux. Relisez et modifiez le texte avant de l’enregistrer.'
          : 'Proposition générée. Relisez et modifiez le texte avant de l’enregistrer.';
        }).catch(function (error) {
          status.textContent = error.message || 'La génération a échoué. Réessayez.';
        });
      });
    }

    if (tagButton) {
      var tagStatus = document.querySelector('[data-tag-status]');
      var results = document.querySelector('[data-tag-results]');
      tagButton.addEventListener('click', function () {
        tagStatus.textContent = 'Analyse du titre et de la description…';
        requestJson(tagButton.getAttribute('data-endpoint'), getFormValues(), tagButton, tagStatus).then(function (data) {
          results.textContent = '';
          results.hidden = false;
          if (!data.category && !data.tags.length) {
            tagStatus.textContent = 'Aucune catégorie ni tag pertinent détecté. Ajoutez des mots-clés écologiques au texte.';
            results.hidden = true;
            return;
          }

          if (data.category) {
            var categoryButton = document.createElement('button');
            categoryButton.type = 'button';
            categoryButton.className = 'btn btn-secondary btn-sm';
            categoryButton.textContent = 'Appliquer la catégorie : ' + data.category_label;
            categoryButton.addEventListener('click', function () {
              form.elements.namedItem('category').value = data.category;
              tagStatus.textContent = 'Catégorie appliquée. Vérifiez le formulaire avant de l’enregistrer.';
            });
            results.appendChild(categoryButton);
          }

          if (data.tags.length) {
            var tagsButton = document.createElement('button');
            tagsButton.type = 'button';
            tagsButton.className = 'btn btn-secondary btn-sm';
            tagsButton.textContent = 'Ajouter les tags : ' + data.tags.join(' ');
            tagsButton.addEventListener('click', function () {
              var text = description.value;
              var newTags = data.tags.filter(function (tag) {
                return text.toLowerCase().indexOf(tag.toLowerCase()) === -1;
              });
              if (newTags.length) {
                description.value = (text.trim() ? text.trim() + '\n\n' : '') + newTags.join(' ');
                description.dispatchEvent(new Event('input', { bubbles: true }));
              }
              tagStatus.textContent = newTags.length
                ? 'Tags ajoutés à la description. Modifiez-les si besoin avant l’enregistrement.'
                : 'Ces tags sont déjà présents dans la description.';
            });
            results.appendChild(tagsButton);
          }
          tagStatus.textContent = 'Suggestions locales prêtes : choisissez la catégorie et/ou les tags à appliquer.';
        }).catch(function (error) {
          tagStatus.textContent = error.message || 'Impossible de suggérer des tags.';
        });
      });
    }
  });
})();
