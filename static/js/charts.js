/* EcoTeams — tiny dependency-free SVG charts.
   Usage: <div data-chart="bar|line|hbar|donut" data-source="json-script-id" data-unit="pts"></div>
   Data: [{"label": "…", "value": 12, "tone": "success"}, …] produced by Django's json_script. */
(function () {
  'use strict';

  var NS = 'http://www.w3.org/2000/svg';
  var TONES = {
    lime: '#B7FF4A', success: '#22C55E', emerald: '#22C55E', cyan: '#42E8D5', info: '#42E8D5', blue: '#5B8CFF',
    violet: '#9B87F5', warning: '#FFC857', amber: '#FFC857', danger: '#FF6B6B', gold: '#FFD166', muted: '#8C98B5',
  };
  // Categorical palette: ecology (green), technology (cyan / blue), insight (violet), attention (amber).
  var PALETTE = ['#22C55E', '#5B8CFF', '#42E8D5', '#FFC857', '#9B87F5', '#B7FF4A', '#FF8FA3', '#7DD3FC'];

  function cssVar(name, fallback) {
    var value = getComputedStyle(document.body).getPropertyValue(name).trim();
    return value || fallback;
  }

  function node(name, attrs, parent) {
    var element = document.createElementNS(NS, name);
    Object.keys(attrs || {}).forEach(function (key) { element.setAttribute(key, attrs[key]); });
    if (parent) { parent.appendChild(element); }
    return element;
  }

  function format(value, unit) {
    var text = Number(value).toLocaleString('fr-FR', { maximumFractionDigits: 1 });
    return unit ? text + ' ' + unit : text;
  }

  function niceMax(value) {
    if (value <= 0) { return 1; }
    var power = Math.pow(10, Math.floor(Math.log(value) / Math.LN10));
    var n = value / power;
    var nice = n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10;
    return nice * power;
  }

  function addDefs(svg) {
    var defs = node('defs', {}, svg);
    var bar = node('linearGradient', { id: 'eco-bar-gradient', x1: '0', y1: '0', x2: '0', y2: '1' }, defs);
    node('stop', { offset: '0%', 'stop-color': cssVar('--accent', '#B7FF4A') }, bar);
    node('stop', { offset: '100%', 'stop-color': cssVar('--accent-2', '#42E8D5'), 'stop-opacity': '0.75' }, bar);
    var area = node('linearGradient', { id: 'eco-area-gradient', x1: '0', y1: '0', x2: '0', y2: '1' }, defs);
    node('stop', { offset: '0%', 'stop-color': cssVar('--accent', '#B7FF4A'), 'stop-opacity': '0.28' }, area);
    node('stop', { offset: '100%', 'stop-color': cssVar('--accent', '#B7FF4A'), 'stop-opacity': '0' }, area);
  }

  function tooltip(container) {
    var tip = container.querySelector('.chart-tip');
    if (!tip) {
      tip = document.createElement('div');
      tip.className = 'chart-tip';
      tip.setAttribute('role', 'status');
      container.appendChild(tip);
    }
    return {
      show: function (x, y, label, value) {
        tip.innerHTML = '';
        var strong = document.createElement('strong');
        strong.textContent = value;
        tip.appendChild(document.createTextNode(label + ' · '));
        tip.appendChild(strong);
        tip.style.left = x + 'px';
        tip.style.top = y + 'px';
        tip.classList.add('visible');
      },
      hide: function () { tip.classList.remove('visible'); },
    };
  }

  function bindTip(target, tip, x, y, label, valueText) {
    target.setAttribute('tabindex', '0');
    var show = function () { tip.show(x, y, label, valueText); };
    target.addEventListener('mouseenter', show);
    target.addEventListener('focus', show);
    target.addEventListener('mouseleave', tip.hide);
    target.addEventListener('blur', tip.hide);
    node('title', {}, target).textContent = label + ' : ' + valueText;
  }

  function frame(container, data, opts, height) {
    var width = Math.max(260, container.clientWidth || 600);
    var pad = { top: 14, right: 10, bottom: 30, left: 44 };
    var svg = node('svg', { viewBox: '0 0 ' + width + ' ' + height, role: 'img', 'aria-label': opts.label || 'Graphique' });
    addDefs(svg);
    var values = data.map(function (d) { return Number(d.value) || 0; });
    var max = niceMax(Math.max.apply(null, values.concat([0])));
    if (values.every(function (v) { return v === Math.round(v); })) {
      max = Math.max(4, Math.ceil(max / 4) * 4);  // whole-number ticks for counts and points
    }
    var innerW = width - pad.left - pad.right;
    var innerH = height - pad.top - pad.bottom;
    for (var i = 0; i <= 4; i++) {
      var y = pad.top + innerH - (innerH * i / 4);
      node('line', { class: 'grid-line', x1: pad.left, x2: width - pad.right, y1: y, y2: y }, svg);
      node('text', { class: 'axis-label', x: pad.left - 8, y: y + 4, 'text-anchor': 'end' }, svg).textContent =
        format(max * i / 4);
    }
    var every = Math.ceil(data.length / Math.max(1, Math.floor(innerW / 64)));
    return { svg: svg, width: width, pad: pad, max: max, innerW: innerW, innerH: innerH, values: values, every: every };
  }

  function renderBar(container, data, opts) {
    var f = frame(container, data, opts, opts.height || 240);
    var tip = tooltip(container);
    var slot = f.innerW / data.length;
    var barW = Math.max(6, Math.min(42, slot * 0.58));
    data.forEach(function (d, i) {
      var value = Math.max(0, f.values[i]);
      var h = f.innerH * value / f.max;
      var x = f.pad.left + slot * i + (slot - barW) / 2;
      var y = f.pad.top + f.innerH - h;
      var bar = node('rect', { class: 'bar', x: x, y: y, width: barW, height: Math.max(h, value ? 2 : 0), rx: Math.min(7, barW / 2) }, f.svg);
      bindTip(bar, tip, x + barW / 2, y, d.label, format(d.value, opts.unit));
      if (i % f.every === 0) {
        node('text', { class: 'axis-label', x: x + barW / 2, y: f.pad.top + f.innerH + 18, 'text-anchor': 'middle' }, f.svg).textContent = d.label;
      }
    });
    container.appendChild(f.svg);
  }

  function renderLine(container, data, opts) {
    var f = frame(container, data, opts, opts.height || 240);
    var tip = tooltip(container);
    var step = data.length > 1 ? f.innerW / (data.length - 1) : 0;
    var points = data.map(function (d, i) {
      var value = Math.max(0, f.values[i]);
      return [f.pad.left + step * i, f.pad.top + f.innerH - f.innerH * value / f.max];
    });
    var line = points.map(function (p, i) { return (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1); }).join(' ');
    var baseline = f.pad.top + f.innerH;
    node('path', { class: 'area', d: line + ' L' + points[points.length - 1][0] + ' ' + baseline + ' L' + points[0][0] + ' ' + baseline + ' Z' }, f.svg);
    node('path', { class: 'line', d: line }, f.svg);
    points.forEach(function (p, i) {
      var dot = node('circle', { class: 'point', cx: p[0], cy: p[1], r: 4.5 }, f.svg);
      bindTip(dot, tip, p[0], p[1], data[i].label, format(data[i].value, opts.unit));
      if (i % f.every === 0) {
        node('text', { class: 'axis-label', x: p[0], y: baseline + 18, 'text-anchor': 'middle' }, f.svg).textContent = data[i].label;
      }
    });
    container.appendChild(f.svg);
  }

  function fitLabel(text, pixels) {
    var maxChars = Math.max(4, Math.floor(pixels / 6.4));
    return text.length > maxChars ? text.slice(0, maxChars - 1) + '…' : text;
  }

  function renderHBar(container, data, opts) {
    var width = Math.max(240, container.clientWidth || 600);
    // Narrow cards: label on its own line above the bar, so long labels never overlap.
    var stacked = width < 460;
    var rowH = stacked ? 42 : 34;
    var labelW = stacked ? 0 : Math.min(200, width * 0.34);
    var valueW = 64;
    var height = data.length * rowH + 6;
    var svg = node('svg', { viewBox: '0 0 ' + width + ' ' + height, role: 'img', 'aria-label': opts.label || 'Graphique' });
    addDefs(svg);
    var tip = tooltip(container);
    var max = Math.max.apply(null, data.map(function (d) { return Number(d.value) || 0; }).concat([0])) || 1;
    var barSpace = width - labelW - valueW - (stacked ? 0 : 12);
    data.forEach(function (d, i) {
      var y = i * rowH + 6;
      var barY = stacked ? y + 20 : y + 4;
      var value = Math.max(0, Number(d.value) || 0);
      var label = node('text', { class: 'axis-label', x: 0, y: y + (stacked ? 11 : 16) }, svg);
      label.textContent = fitLabel(d.label, stacked ? width - valueW : labelW - 10);
      node('rect', { x: labelW, y: barY, width: barSpace, height: 14, rx: 7, fill: 'rgba(244,247,251,0.06)' }, svg);
      var bar = node('rect', { class: 'bar', x: labelW, y: barY, width: Math.max(value ? 4 : 0, barSpace * value / max), height: 14, rx: 7 }, svg);
      if (d.tone && TONES[d.tone]) { bar.setAttribute('style', 'fill:' + TONES[d.tone]); }
      else if (opts.multicolor) { bar.setAttribute('style', 'fill:' + PALETTE[i % PALETTE.length]); }
      bindTip(bar, tip, labelW + barSpace * value / max, barY, d.label, format(d.value, opts.unit));
      node('text', { class: 'axis-label', x: width, y: barY + 12, 'text-anchor': 'end', style: 'fill:#F4F7FB;font-weight:600' }, svg).textContent = format(d.value, opts.unit);
    });
    container.appendChild(svg);
  }

  function renderDonut(container, data, opts) {
    var total = data.reduce(function (sum, d) { return sum + (Number(d.value) || 0); }, 0);
    var wrap = document.createElement('div');
    wrap.className = 'donut-wrap';
    var size = 160;
    var radius = 62;
    var circumference = 2 * Math.PI * radius;
    var svg = node('svg', { viewBox: '0 0 ' + size + ' ' + size, width: size, height: size, role: 'img', 'aria-label': opts.label || 'Répartition' });
    node('circle', { cx: size / 2, cy: size / 2, r: radius, fill: 'none', stroke: 'rgba(244,247,251,0.06)', 'stroke-width': 18 }, svg);
    var offset = 0;
    var tip = tooltip(container);
    data.forEach(function (d, i) {
      var value = Number(d.value) || 0;
      if (!value) { return; }
      var length = circumference * value / total;
      var color = TONES[d.tone] || PALETTE[i % PALETTE.length];
      var arc = node('circle', {
        cx: size / 2, cy: size / 2, r: radius, fill: 'none', stroke: color, 'stroke-width': 18,
        'stroke-dasharray': length + ' ' + (circumference - length), 'stroke-dashoffset': -offset,
        transform: 'rotate(-90 ' + size / 2 + ' ' + size / 2 + ')', style: 'cursor:pointer',
      }, svg);
      bindTip(arc, tip, size / 2, 20, d.label, format(value, opts.unit) + ' (' + Math.round(value * 100 / total) + ' %)');
      offset += length;
    });
    var center = node('text', { x: size / 2, y: size / 2 + 2, 'text-anchor': 'middle', style: 'fill:#F4F7FB;font:700 22px var(--font-display)' }, svg);
    center.textContent = format(total);
    node('text', { x: size / 2, y: size / 2 + 20, 'text-anchor': 'middle', class: 'axis-label' }, svg).textContent = opts.centerLabel || 'total';
    wrap.appendChild(svg);
    var legend = document.createElement('div');
    legend.className = 'chart-legend';
    legend.style.flexDirection = 'column';
    data.forEach(function (d, i) {
      var item = document.createElement('span');
      var swatch = document.createElement('i');
      swatch.style.background = TONES[d.tone] || PALETTE[i % PALETTE.length];
      item.appendChild(swatch);
      item.appendChild(document.createTextNode(d.label + ' — ' + format(d.value, opts.unit)));
      legend.appendChild(item);
    });
    wrap.appendChild(legend);
    container.appendChild(wrap);
  }

  var RENDERERS = { bar: renderBar, line: renderLine, hbar: renderHBar, donut: renderDonut };

  function render(container) {
    var source = document.getElementById(container.getAttribute('data-source'));
    var renderer = RENDERERS[container.getAttribute('data-chart')];
    if (!source || !renderer) { return; }
    var data;
    try { data = JSON.parse(source.textContent); } catch (e) { data = []; }
    container.innerHTML = '';
    var hasData = data.length && data.some(function (d) { return Number(d.value) > 0; });
    if (!hasData) {
      var empty = document.createElement('div');
      empty.className = 'chart-empty';
      empty.textContent = container.getAttribute('data-empty') || 'Pas encore de données pour cette période.';
      container.appendChild(empty);
      return;
    }
    renderer(container, data, {
      unit: container.getAttribute('data-unit') || '',
      label: container.getAttribute('aria-label') || '',
      centerLabel: container.getAttribute('data-center-label') || '',
      height: parseInt(container.getAttribute('data-height') || '0', 10) || null,
      multicolor: container.hasAttribute('data-multicolor'),
    });
  }

  function renderAll() {
    Array.prototype.forEach.call(document.querySelectorAll('[data-chart]'), render);
  }

  var timer = null;
  window.addEventListener('resize', function () {
    clearTimeout(timer);
    timer = setTimeout(renderAll, 200);
  });
  document.addEventListener('DOMContentLoaded', renderAll);
})();
