/* Local inline SVG line chart for recent weather history. No charting library or CDN. */
(() => {
  'use strict';
  const ns = 'http://www.w3.org/2000/svg';
  const node = (tag, attrs) => {
    const el = document.createElementNS(ns, tag);
    for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
    return el;
  };
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const shortClock = value => new Date(value).toLocaleString('en-SG', {timeZone:'Asia/Singapore', hour:'2-digit', minute:'2-digit', hour12:false});
  const fullClock = value => new Date(value).toLocaleString('en-SG', {timeZone:'Asia/Singapore', hour12:false}) + ' SGT';
  const unitSymbol = unit => unit === 'degC_WBGT' ? '°C' : unit === 'mm' ? ' mm' : '';
  const ageText = minutes => minutes < 1 ? 'just now' : minutes < 60 ? Math.round(minutes) + ' min ago' : (minutes / 60).toFixed(1) + ' h ago';

  function render(containerId, {points, unit, forecast, stationLabel, stationId}) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    const symbol = unitSymbol(unit);

    if (!points.length) {
      const empty = document.createElement('div');
      empty.className = 'chart-empty';
      empty.textContent = `No ${esc(stationLabel || stationId)} observations collected yet. Run ingestion to build history.`;
      container.append(empty);
      return;
    }

    const last = points[points.length - 1];
    const ageMinutes = (Date.now() - new Date(last.observed_at).getTime()) / 60000;
    const summary = document.createElement('div');
    summary.className = 'chart-summary';
    summary.textContent = `${points.length} observation${points.length === 1 ? '' : 's'} from ${shortClock(points[0].observed_at)} to ${shortClock(last.observed_at)} SGT. `
      + `Latest ${last.value.toFixed(1)}${symbol} (${ageText(ageMinutes)}).`
      + (forecast ? ` Forecast +1h: ${forecast.value.toFixed(1)}${symbol} (persistence baseline, not trained AI).` : ' No forecast available for this station right now.');
    container.append(summary);

    if (points.length < 5) {
      const note = document.createElement('div');
      note.className = 'chart-note';
      note.textContent = 'Limited history so far: the trend line will become more informative as more readings are collected.';
      container.append(note);
    }

    const wrap = document.createElement('div');
    wrap.className = 'chart-wrap';
    container.append(wrap);

    const width = 640, height = 220, padLeft = 46, padRight = 18, padTop = 16, padBottom = 26;
    const series = forecast ? [...points, forecast] : points;
    const times = series.map(p => new Date(p.observed_at).getTime());
    const values = series.map(p => p.value);
    const minT = Math.min(...times), maxT = Math.max(...times);
    const minV = Math.min(...values), maxV = Math.max(...values);
    const padV = (maxV - minV) * 0.2 || 1;
    const vLow = minV - padV, vHigh = maxV + padV;
    const x = t => padLeft + (maxT === minT ? (width - padLeft - padRight) / 2 : (t - minT) / (maxT - minT) * (width - padLeft - padRight));
    const y = v => padTop + (1 - (v - vLow) / (vHigh - vLow)) * (height - padTop - padBottom);

    const svg = node('svg', {
      viewBox: `0 0 ${width} ${height}`, role: 'img',
      'aria-label': `${stationLabel || stationId} trend: ${points.length} observations, latest ${last.value.toFixed(1)}${symbol}`
        + (forecast ? `, one-hour persistence forecast ${forecast.value.toFixed(1)}${symbol}` : ''),
    });

    const gridCount = 4;
    for (let i = 0; i <= gridCount; i++) {
      const v = vLow + (vHigh - vLow) * i / gridCount;
      const yy = y(v);
      svg.append(node('line', {x1: padLeft, x2: width - padRight, y1: yy.toFixed(1), y2: yy.toFixed(1), class: 'chart-grid'}));
      const label = node('text', {x: padLeft - 6, y: (yy + 4).toFixed(1), class: 'chart-axis-text', 'text-anchor': 'end'});
      label.textContent = v.toFixed(1);
      svg.append(label);
    }

    const xTickSource = [points[0], points[Math.floor((points.length - 1) / 2)], last];
    new Set(xTickSource).forEach(p => {
      const xx = x(new Date(p.observed_at).getTime());
      const label = node('text', {x: xx.toFixed(1), y: height - 8, class: 'chart-axis-text', 'text-anchor': 'middle'});
      label.textContent = shortClock(p.observed_at);
      svg.append(label);
    });

    if (points.length >= 2) {
      const baseline = y(vLow);
      const areaPoints = points.map(p => `${x(new Date(p.observed_at).getTime()).toFixed(1)},${y(p.value).toFixed(1)}`);
      const areaD = `M${areaPoints.join('L')}L${x(new Date(last.observed_at).getTime()).toFixed(1)},${baseline.toFixed(1)}`
        + `L${x(new Date(points[0].observed_at).getTime()).toFixed(1)},${baseline.toFixed(1)}Z`;
      svg.append(node('path', {d: areaD, class: 'chart-fill'}));
    }

    const lineD = points.map((p, i) => `${i ? 'L' : 'M'}${x(new Date(p.observed_at).getTime()).toFixed(1)},${y(p.value).toFixed(1)}`).join('');
    svg.append(node('path', {d: lineD, class: 'chart-line'}));

    const lastX = x(new Date(last.observed_at).getTime()), lastY = y(last.value);
    if (forecast) {
      const forecastX = x(new Date(forecast.observed_at).getTime()), forecastY = y(forecast.value);
      svg.append(node('line', {x1: lastX.toFixed(1), y1: lastY.toFixed(1), x2: forecastX.toFixed(1), y2: forecastY.toFixed(1), class: 'chart-forecast-line'}));
      svg.append(node('circle', {cx: forecastX.toFixed(1), cy: forecastY.toFixed(1), r: 4, class: 'chart-marker-forecast'}));
      const forecastLabel = node('text', {
        x: forecastX.toFixed(1), y: (forecastY - 10).toFixed(1), class: 'chart-label-forecast',
        'text-anchor': forecastX > width - 70 ? 'end' : 'middle',
      });
      forecastLabel.textContent = `Forecast ${forecast.value.toFixed(1)}${symbol}`;
      svg.append(forecastLabel);
    }
    svg.append(node('circle', {cx: lastX.toFixed(1), cy: lastY.toFixed(1), r: 4, class: 'chart-marker-observed'}));
    const lastLabel = node('text', {
      x: lastX.toFixed(1), y: (lastY - 10).toFixed(1), class: 'chart-label',
      'text-anchor': forecast ? 'end' : (lastX > width - 70 ? 'end' : 'middle'),
    });
    lastLabel.textContent = `${last.value.toFixed(1)}${symbol}`;
    svg.append(lastLabel);

    // Hover crosshair + tooltip: snaps to the nearest point on pointer move, mirrors on focus for keyboard/touch.
    const crosshair = node('line', {class: 'chart-crosshair', y1: padTop, y2: height - padBottom, x1: -100, x2: -100});
    svg.append(crosshair);
    const hit = node('rect', {x: padLeft, y: padTop, width: Math.max(1, width - padLeft - padRight), height: height - padTop - padBottom, class: 'chart-hit'});
    svg.append(hit);
    const tooltip = document.createElement('div');
    tooltip.className = 'chart-tooltip';
    tooltip.hidden = true;
    wrap.append(svg, tooltip);

    function showAt(clientX) {
      const rect = svg.getBoundingClientRect();
      const scale = width / rect.width;
      const svgX = (clientX - rect.left) * scale;
      const t = minT + Math.max(0, Math.min(1, (svgX - padLeft) / (width - padLeft - padRight))) * (maxT - minT);
      let nearest = series[0];
      for (const p of series) if (Math.abs(new Date(p.observed_at).getTime() - t) < Math.abs(new Date(nearest.observed_at).getTime() - t)) nearest = p;
      const nx = x(new Date(nearest.observed_at).getTime());
      crosshair.setAttribute('x1', nx.toFixed(1));
      crosshair.setAttribute('x2', nx.toFixed(1));
      const isForecast = forecast && nearest === forecast;
      tooltip.hidden = false;
      tooltip.textContent = `${fullClock(nearest.observed_at)}: ${nearest.value.toFixed(1)}${symbol}${isForecast ? ' (forecast)' : ''}`;
      const wrapRect = wrap.getBoundingClientRect();
      tooltip.style.left = ((nx / width) * wrapRect.width) + 'px';
      tooltip.style.top = (y(nearest.value) / height) * wrapRect.height + 'px';
    }
    function hide() { crosshair.setAttribute('x1', -100); crosshair.setAttribute('x2', -100); tooltip.hidden = true; }
    hit.addEventListener('pointermove', event => showAt(event.clientX));
    hit.addEventListener('pointerleave', hide);
    hit.addEventListener('pointerdown', event => showAt(event.clientX));
    hit.setAttribute('tabindex', '0');
    hit.setAttribute('role', 'application');
    hit.setAttribute('aria-label', 'Chart data; use the table below for a non-visual view');

    const details = document.createElement('details');
    const summaryEl = document.createElement('summary');
    summaryEl.textContent = 'View as table';
    const table = document.createElement('table');
    table.innerHTML = '<thead><tr><th>Observed at (SGT)</th><th>Value</th></tr></thead>';
    const tbody = document.createElement('tbody');
    for (const p of points) {
      const tr = document.createElement('tr');
      const t1 = document.createElement('td'), t2 = document.createElement('td');
      t1.textContent = fullClock(p.observed_at);
      t2.textContent = `${p.value.toFixed(1)}${symbol}`;
      tr.append(t1, t2);
      tbody.append(tr);
    }
    if (forecast) {
      const tr = document.createElement('tr');
      const t1 = document.createElement('td'), t2 = document.createElement('td');
      t1.textContent = fullClock(forecast.observed_at) + ' (forecast)';
      t2.textContent = `${forecast.value.toFixed(1)}${symbol}`;
      tr.append(t1, t2);
      tbody.append(tr);
    }
    table.append(tbody);
    details.append(summaryEl, table);
    container.append(details);
  }

  window.heatChart = {render};
})();
