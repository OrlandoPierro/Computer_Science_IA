'use strict';

// The only asynchronous application request: the existing advice endpoint.
const adviceForm = document.getElementById('advice-form');
if (adviceForm) {
  const result = document.getElementById('advice-result');
  const submit = adviceForm.querySelector('button[type="submit"]');
  let controller = null;
  let revision = 0;
  adviceForm.addEventListener('input', () => {
    revision += 1;
    if (controller) controller.abort();
    result.className = 'advice-result';
    result.textContent = 'Details changed. Calculate again for the updated assessment.';
  });
  adviceForm.addEventListener('submit', async event => {
    event.preventDefault();
    if (!adviceForm.reportValidity()) return;
    const requestRevision = revision;
    controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    submit.disabled = true;
    submit.textContent = 'Calculating…';
    adviceForm.setAttribute('aria-busy', 'true');
    result.className = 'advice-result is-loading';
    result.textContent = 'Calculating the minimum required score…';
    try {
      const response = await fetch(adviceForm.action, {
        method: 'POST', body: new FormData(adviceForm), credentials: 'same-origin',
        headers: {Accept: 'application/json'}, signal: controller.signal
      });
      const data = await response.json();
      if (requestRevision !== revision) return;
      if (!response.ok || data.error) {
        throw new Error(response.status === 401 ? 'Your session has expired. Log in again to calculate advice.' : (data.error || 'Unable to calculate advice. Please try again.'));
      }
      const required = data.required_percentage;
      if (typeof required === 'number' && Number.isFinite(required)) {
        // Round up so the displayed minimum is sufficient.
        const minimum = Math.ceil(required * 100) / 100;
        result.textContent = required === 0
          ? 'Minimum required: 0%. The model reaches your target even with a zero score on this proposed assessment.'
          : `Minimum required: ${minimum.toFixed(2)}% on this assessment to reach your target predicted grade.`;
      } else if (typeof required === 'string') {
        result.textContent = required;
      } else {
        throw new Error('The server returned an unexpected result. Please try again.');
      }
      result.className = 'advice-result';
    } catch (error) {
      if (requestRevision !== revision) return;
      result.className = 'advice-result is-error';
      result.textContent = error.name === 'AbortError'
        ? 'The request took too long. Please try again.'
        : error instanceof TypeError || error instanceof SyntaxError
          ? 'Could not contact the server or read its response. Please try again.' : error.message;
    } finally {
      clearTimeout(timeout);
      controller = null;
      submit.disabled = false;
      submit.textContent = 'Calculate required score';
      adviceForm.removeAttribute('aria-busy');
    }
  });
}

// SVG chart with a true date axis. All data comes from Jinja, without a request.
const chartElement = document.getElementById('trajectory-chart');
const chartDataElement = document.getElementById('chart-data');
if (chartElement && chartDataElement) {
  const data = JSON.parse(chartDataElement.textContent);
  const namespace = 'http://www.w3.org/2000/svg';
  const node = (tag, attributes = {}, text = '') => {
    const element = document.createElementNS(namespace, tag);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
    if (text) element.textContent = text;
    return element;
  };
  const timestamp = date => Date.parse(date + 'T00:00:00Z');
  const formatDate = time => new Date(time).toLocaleDateString('en-GB', {day:'numeric', month:'short', year:'2-digit', timeZone:'UTC'});
  const renderChart = () => {
    const width = Math.max(270, chartElement.clientWidth);
    const height = width < 500 ? 250 : 290;
    const margin = {left:43, right:16, top:22, bottom:48};
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const assessments = data.assessments;
    const times = assessments.map(item => timestamp(item.date));
    let minDate = times.length ? Math.min(...times) : Date.UTC(2026, 0, 1);
    let maxDate = times.length ? Math.max(...times) : minDate + 86400000;
    if (minDate === maxDate) { minDate -= 86400000; maxDate += 86400000; }
    const x = time => margin.left + (time - minDate) / (maxDate - minDate) * plotWidth;
    const y = percentage => margin.top + (100 - percentage) / 100 * plotHeight;
    const svg = node('svg', {viewBox:`0 0 ${width} ${height}`, role:'group', 'aria-labelledby':'chart-title chart-description'});
    svg.append(node('title', {id:'chart-title'}, 'Assessment score trajectory'));
    svg.append(node('desc', {id:'chart-description'}, 'Percentage scores from 0 to 100, plotted by date. Each assessment point opens a delete confirmation. The line shows the backend weighted regression.'));
    for (let percent = 0; percent <= 100; percent += 25) {
      svg.append(node('line', {x1:margin.left, y1:y(percent), x2:width-margin.right, y2:y(percent), class:'chart-grid'}));
      svg.append(node('text', {x:margin.left-10, y:y(percent)+4, 'text-anchor':'end', class:'chart-axis-text'}, String(percent)));
    }
    svg.append(node('text', {x:margin.left, y:12, class:'chart-axis-text'}, '%'));
    if (times.length) {
      const tickCount = width < 500 ? 2 : 4;
      for (let i = 0; i < tickCount; i++) {
        const time = minDate + (maxDate-minDate) * i / (tickCount-1);
        svg.append(node('text', {x:x(time), y:height-23, 'text-anchor':i===0?'start':i===tickCount-1?'end':'middle', class:'chart-axis-text'}, formatDate(time)));
      }
    }
    svg.append(node('text', {x:width-margin.right, y:height-3, 'text-anchor':'end', class:'chart-axis-text'}, 'Time →'));
    if (data.regression.length > 1) {
      const points = data.regression.map((percentage, index) => `${x(timestamp(data.dates[index]))},${y(percentage)}`).join(' ');
      svg.append(node('polyline', {points, class:'chart-trend'}));
    }
    // Overlapping points can also be selected independently from the records list.
    assessments.forEach(item => {
      const percent = 100 * item.score / item.maximum;
      const label = `${item.date}, ${item.type}: ${item.score} out of ${item.maximum}, ${percent.toFixed(1)} percent. Select to delete.`;
      const point = node('g', {class:'chart-point', transform:`translate(${x(timestamp(item.date))} ${y(percent)})`, tabindex:'0', role:'button', 'aria-label':label});
      point.append(node('title', {}, label));
      point.append(node('circle', {r:14, class:'point-ring'}));
      point.append(node('circle', {r:4.5, fill:'#245747', stroke:'#fff', 'stroke-width':1.5}));
      point.append(node('circle', {r:14, fill:'transparent'}));
      const openConfirmation = () => document.getElementById(`delete-assessment-${item.id}`).requestSubmit();
      point.addEventListener('click', openConfirmation);
      point.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); openConfirmation(); }
      });
      svg.append(point);
    });
    chartElement.replaceChildren(svg);
  };
  let lastWidth = 0;
  new ResizeObserver(entries => {
    const width = entries[0].contentRect.width;
    if (Math.abs(width-lastWidth) > 1) { lastWidth = width; renderChart(); }
  }).observe(chartElement);
  renderChart();
}
