/* EcoTeams — interface behaviours (vanilla JS, progressive enhancement).
   Every feature works without JavaScript; these scripts only improve comfort. */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function $all(selector, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(selector));
  }

  /* Sidebar (mobile) */
  function initSidebar() {
    var body = document.body;
    $all('[data-sidebar-toggle]').forEach(function (button) {
      button.addEventListener('click', function () {
        var open = body.classList.toggle('sidebar-open');
        button.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    });
    $all('[data-sidebar-close]').forEach(function (el) {
      el.addEventListener('click', function () { body.classList.remove('sidebar-open'); });
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') { body.classList.remove('sidebar-open'); }
    });
  }

  /* Dropdowns (notifications, user menu) */
  function initDropdowns() {
    var dropdowns = $all('[data-dropdown]');
    function closeAll(except) {
      dropdowns.forEach(function (dd) {
        if (dd !== except) {
          dd.classList.remove('open');
          var trigger = dd.querySelector('[data-dropdown-trigger]');
          if (trigger) { trigger.setAttribute('aria-expanded', 'false'); }
        }
      });
    }
    dropdowns.forEach(function (dd) {
      var trigger = dd.querySelector('[data-dropdown-trigger]');
      if (!trigger) { return; }
      trigger.addEventListener('click', function (event) {
        event.stopPropagation();
        var open = !dd.classList.contains('open');
        closeAll(dd);
        dd.classList.toggle('open', open);
        trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    });
    document.addEventListener('click', function (event) {
      if (!event.target.closest('[data-dropdown]')) { closeAll(); }
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') { closeAll(); }
    });
  }

  /* Toast messages */
  function initToasts() {
    $all('.toast').forEach(function (toast, index) {
      function dismiss() {
        toast.classList.add('is-leaving');
        setTimeout(function () { toast.remove(); }, 320);
      }
      var close = toast.querySelector('.toast-close');
      if (close) { close.addEventListener('click', dismiss); }
      if (!toast.classList.contains('error')) {
        setTimeout(dismiss, 6000 + index * 600);
      }
    });
  }

  /* Confirmation before sensitive POST forms */
  function initConfirm() {
    document.addEventListener('submit', function (event) {
      var form = event.target;
      var submitter = event.submitter;
      var message = (submitter && submitter.getAttribute('data-confirm')) || form.getAttribute('data-confirm');
      if (message && !window.confirm(message)) {
        event.preventDefault();
      }
    }, true);
  }

  /* Prevent double submissions (the server also enforces idempotency) */
  function initSubmitLock() {
    document.addEventListener('submit', function (event) {
      var form = event.target;
      if (event.defaultPrevented || form.hasAttribute('data-no-lock') || form.method.toLowerCase() !== 'post') { return; }
      var submitter = event.submitter;
      // Deferred so the browser has already captured the clicked button's name/value.
      setTimeout(function () {
        $all('button[type="submit"], button:not([type])', form).forEach(function (button) {
          button.disabled = true;
          if (button === submitter) { button.classList.add('is-loading'); }
        });
      }, 0);
    });
  }

  /* Image preview for uploads */
  function initImagePreview() {
    $all('input[type="file"][data-preview]').forEach(function (input) {
      var preview = document.createElement('img');
      preview.className = 'image-preview';
      preview.alt = 'Aperçu de l’image sélectionnée';
      input.insertAdjacentElement('afterend', preview);
      input.addEventListener('change', function () {
        var file = input.files && input.files[0];
        if (!file || !/^image\//.test(file.type)) { preview.classList.remove('visible'); return; }
        var reader = new FileReader();
        reader.onload = function (e) { preview.src = e.target.result; preview.classList.add('visible'); };
        reader.readAsDataURL(file);
      });
    });
  }

  /* Password visibility toggle */
  function initPasswordToggle() {
    $all('input[type="password"]').forEach(function (input) {
      var wrap = document.createElement('div');
      wrap.className = 'password-wrap';
      input.parentNode.insertBefore(wrap, input);
      wrap.appendChild(input);
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'password-toggle';
      button.setAttribute('aria-label', 'Afficher le mot de passe');
      button.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>';
      button.addEventListener('click', function () {
        var visible = input.type === 'text';
        input.type = visible ? 'password' : 'text';
        button.setAttribute('aria-label', visible ? 'Afficher le mot de passe' : 'Masquer le mot de passe');
      });
      wrap.appendChild(button);
    });
  }

  /* Character counters */
  function initCharCount() {
    $all('textarea[maxlength]').forEach(function (area) {
      var max = parseInt(area.getAttribute('maxlength'), 10);
      var counter = document.createElement('div');
      counter.className = 'char-count';
      area.insertAdjacentElement('afterend', counter);
      function update() { counter.textContent = area.value.length + ' / ' + max; }
      area.addEventListener('input', update);
      update();
    });
  }

  /* Auto-submit filter forms when a select changes */
  function initAutoSubmit() {
    $all('form[data-autosubmit]').forEach(function (form) {
      $all('select, input[type="checkbox"]', form).forEach(function (input) {
        input.addEventListener('change', function () { form.submit(); });
      });
    });
  }

  /* Client-side filtering of long checkbox lists */
  function initListFilter() {
    $all('[data-filter-input]').forEach(function (input) {
      var target = document.querySelector(input.getAttribute('data-filter-input'));
      if (!target) { return; }
      input.addEventListener('input', function () {
        var query = input.value.trim().toLowerCase();
        $all('[data-filter-item]', target).forEach(function (item) {
          item.style.display = item.textContent.toLowerCase().indexOf(query) === -1 ? 'none' : '';
        });
      });
    });
    $all('[data-check-all]').forEach(function (button) {
      button.addEventListener('click', function () {
        var target = document.querySelector(button.getAttribute('data-check-all'));
        var state = button.getAttribute('data-state') !== 'on';
        $all('[data-filter-item]', target).forEach(function (item) {
          if (item.style.display === 'none') { return; }
          var box = item.querySelector('input[type="checkbox"]');
          if (box) { box.checked = state; }
        });
        button.setAttribute('data-state', state ? 'on' : 'off');
      });
    });
  }

  /* Animated counters and progress */
  function animateCount(el) {
    var target = parseFloat(el.getAttribute('data-count-to'));
    if (isNaN(target)) { return; }
    var decimals = parseInt(el.getAttribute('data-decimals') || '0', 10);
    var format = function (value) {
      return value.toLocaleString('fr-FR', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
    };
    if (reduceMotion) { el.textContent = format(target); return; }
    var start = null;
    var duration = 1100;
    function step(ts) {
      if (start === null) { start = ts; }
      var progress = Math.min(1, (ts - start) / duration);
      var eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = format(target * eased);
      if (progress < 1) { window.requestAnimationFrame(step); }
    }
    window.requestAnimationFrame(step);
  }

  function initReveal() {
    var targets = $all('[data-count-to], .reveal, .ring-value[data-offset], .progress-bar[data-width]');
    function show(el) {
      if (el.hasAttribute('data-count-to')) { animateCount(el); }
      if (el.classList.contains('reveal')) { el.classList.add('visible'); }
      if (el.hasAttribute('data-offset')) { el.style.strokeDashoffset = el.getAttribute('data-offset'); }
      if (el.hasAttribute('data-width')) { el.style.width = el.getAttribute('data-width') + '%'; }
    }
    if (!('IntersectionObserver' in window)) { targets.forEach(show); return; }
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { show(entry.target); observer.unobserve(entry.target); }
      });
    }, { threshold: 0.15 });
    targets.forEach(function (el) { observer.observe(el); });
  }

  /* Landing page particle network */
  function initParticles() {
    var canvas = document.querySelector('canvas[data-particles]');
    if (!canvas || reduceMotion || !canvas.getContext) { return; }
    var ctx = canvas.getContext('2d');
    var dots = [];
    var width = 0;
    var height = 0;
    var running = true;
    function resize() {
      var ratio = window.devicePixelRatio || 1;
      width = canvas.offsetWidth;
      height = canvas.offsetHeight;
      canvas.width = width * ratio;
      canvas.height = height * ratio;
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      var count = Math.min(70, Math.floor(width * height / 18000));
      dots = [];
      for (var i = 0; i < count; i++) {
        dots.push({ x: Math.random() * width, y: Math.random() * height, vx: (Math.random() - .5) * .35, vy: (Math.random() - .5) * .35, r: Math.random() * 1.6 + .6 });
      }
    }
    function frame() {
      if (!running) { return; }
      ctx.clearRect(0, 0, width, height);
      for (var i = 0; i < dots.length; i++) {
        var a = dots[i];
        a.x += a.vx; a.y += a.vy;
        if (a.x < 0 || a.x > width) { a.vx *= -1; }
        if (a.y < 0 || a.y > height) { a.vy *= -1; }
        ctx.beginPath();
        ctx.arc(a.x, a.y, a.r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(183,255,74,0.55)';
        ctx.fill();
        for (var j = i + 1; j < dots.length; j++) {
          var b = dots[j];
          var dx = a.x - b.x, dy = a.y - b.y;
          var dist = dx * dx + dy * dy;
          if (dist < 14000) {
            ctx.strokeStyle = 'rgba(66,232,213,' + (0.14 * (1 - dist / 14000)).toFixed(3) + ')';
            ctx.lineWidth = 1;
            ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
          }
        }
      }
      window.requestAnimationFrame(frame);
    }
    document.addEventListener('visibilitychange', function () {
      running = !document.hidden;
      if (running) { window.requestAnimationFrame(frame); }
    });
    window.addEventListener('resize', resize);
    resize();
    window.requestAnimationFrame(frame);
  }

  window.addEventListener('pageshow', function (event) {
    if (event.persisted) {
      $all('button[disabled].is-loading, form button[disabled]').forEach(function (button) {
        button.disabled = false;
        button.classList.remove('is-loading');
      });
    }
  });

  document.addEventListener('DOMContentLoaded', function () {
    initSidebar();
    initDropdowns();
    initToasts();
    initConfirm();
    initSubmitLock();
    initImagePreview();
    initPasswordToggle();
    initCharCount();
    initAutoSubmit();
    initListFilter();
    initReveal();
    initParticles();
  });
})();
