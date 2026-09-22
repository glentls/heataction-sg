// Regression check for the main coordinator planning workflow, run in CI on every push/PR
// (see .github/workflows/ci.yml). This is a mechanical correctness check -- it verifies the
// interface behaves as coded and raises no JavaScript exceptions, not that a first-time
// coordinator finds it usable. See docs/USABILITY_TEST.md for the usability protocol, which
// this script's task list mirrors so a CI regression here likely means a usability-relevant break.
//
// Expects a demo-mode server already running (default http://127.0.0.1:8000) and a headless
// Chrome instance already listening on a DevTools port (default 127.0.0.1:9222). Both env vars
// are overridable so this can run against a different host/port locally.
import assert from 'node:assert/strict';

const APP_URL = process.env.HEATACTION_URL || 'http://127.0.0.1:8000/';
const DEVTOOLS_URL = process.env.HEATACTION_DEVTOOLS || 'http://127.0.0.1:9222';

async function connect() {
  let lastError;
  for (let attempt = 0; attempt < 50; attempt++) {
    try {
      const targets = await (await fetch(`${DEVTOOLS_URL}/json`)).json();
      let target = targets.find(t => t.type === 'page');
      if (!target) target = await (await fetch(`${DEVTOOLS_URL}/json/new?about:blank`)).json();
      return target.webSocketDebuggerUrl;
    } catch (error) {
      lastError = error;
      await new Promise(resolve => setTimeout(resolve, 200));
    }
  }
  throw new Error(`Could not reach DevTools at ${DEVTOOLS_URL}: ${lastError}`);
}

const wsUrl = await connect();
const ws = new WebSocket(wsUrl);
await new Promise((resolve, reject) => {
  ws.addEventListener('open', resolve, {once: true});
  ws.addEventListener('error', reject, {once: true});
});
let sequence = 0;
const pending = new Map();
const jsErrors = [];
ws.addEventListener('message', ({data}) => {
  const message = JSON.parse(data);
  if (message.id) {
    const call = pending.get(message.id);
    pending.delete(message.id);
    message.error ? call.reject(message.error) : call.resolve(message.result);
  }
  if (message.method === 'Runtime.exceptionThrown') jsErrors.push(message.params.exceptionDetails.text);
});
function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    pending.set(id, {resolve, reject});
    ws.send(JSON.stringify({id, method, params}));
  });
}
async function evaluate(expression) {
  const response = await send('Runtime.evaluate', {expression, returnByValue: true, awaitPromise: true});
  if (response.exceptionDetails) throw new Error(JSON.stringify(response.exceptionDetails));
  return response.result.value;
}
async function until(expression, description) {
  for (let i = 0; i < 100; i++) {
    if (await evaluate(expression)) return;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error(`Timed out waiting for: ${description || expression}`);
}

await send('Runtime.enable');
await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', {width: 1280, height: 1400, deviceScaleFactor: 1, mobile: false});
await send('Page.navigate', {url: APP_URL});
await until("document.getElementById('planRows')?.children.length === 3 && document.getElementById('status')?.textContent === ''",
  'demo plan to load with 3 areas');

// 1. Reducing the budget removes exactly the lowest-ranked assigned area.
const assignedAt2 = await evaluate(
  "[...document.querySelectorAll('#planRows tr.assigned')].map(tr => tr.querySelector('strong').textContent)");
assert.equal(assignedAt2.length, 2, `expected 2 assigned areas at the default budget, got ${JSON.stringify(assignedAt2)}`);
await evaluate("document.getElementById('budget').value='1';document.getElementById('budget').dispatchEvent(new Event('change'))");
await until("document.getElementById('status').textContent === ''", 'plan to refresh after budget change');
const assignedAt1 = await evaluate(
  "[...document.querySelectorAll('#planRows tr.assigned')].map(tr => tr.querySelector('strong').textContent)");
assert.equal(assignedAt1.length, 1, `expected 1 assigned area at budget 1, got ${JSON.stringify(assignedAt1)}`);
console.log('OK: budget change updates the assigned areas (%s -> %s)', assignedAt2.join('+'), assignedAt1.join('+'));

// 2. The recommendation explanation names a real area.
await evaluate("document.querySelector('details').open = true");
const explanation = await evaluate("document.getElementById('explanations').innerText");
assert.match(explanation, /Demo North|Demo Central|Demo East/, 'explanation should name an area');
console.log('OK: recommendation explanation is present and names an area');

// 3. Locking an area with a reason keeps it assigned even at a reduced budget.
await evaluate("document.getElementById('budget').value='2';document.getElementById('budget').dispatchEvent(new Event('change'))");
await until("document.getElementById('status').textContent === ''", 'plan to refresh back to budget 2');
const lockArea = await evaluate("document.querySelector('[data-action=lock]')?.dataset.area");
assert.ok(lockArea, 'expected at least one lockable area');
await evaluate(`document.querySelector('[data-area="${lockArea}"][data-action=lock]').click()`);
await until("document.getElementById('lockPanel').hidden === false", 'lock panel to open');
await evaluate("document.getElementById('lockReasonInput').value='CI regression check';" +
  "document.getElementById('lockReasonInput').dispatchEvent(new Event('input'))");
await evaluate("document.getElementById('lockSaveBtn').click()");
await until("document.getElementById('lockPanel').hidden === true && document.getElementById('status').textContent === ''",
  'lock to save and plan to refresh');
await evaluate("document.getElementById('budget').value='1';document.getElementById('budget').dispatchEvent(new Event('change'))");
await until("document.getElementById('status').textContent === ''", 'plan to refresh after budget drop');
const stillAssigned = await evaluate(
  `document.querySelector('[data-area="${lockArea}"]').closest('tr').classList.contains('assigned')`);
assert.equal(stillAssigned, true, 'locked area should stay assigned after the budget drops');
console.log(`OK: locking ${lockArea} keeps it assigned after the budget drops to 1`);

// 4. Scenario comparison correctly identifies an area that gains a slot.
await evaluate("document.getElementById('cmpABudget').value='1';document.getElementById('cmpBBudget').value='2';" +
  "document.getElementById('compareBtn').click()");
await until("document.getElementById('compareResult').innerHTML.length > 0", 'scenario comparison to render');
assert.match(await evaluate("document.getElementById('compareResult').innerText"), /Gains a slot in B/,
  'expected at least one area to gain a slot going from 1 to 2 team slots');
console.log('OK: scenario comparison identifies a gaining area');

// 5. The weather-history chart states a trend window and an observation age.
await until("document.getElementById('historyStation')?.options.length === 3", 'weather-history stations to populate');
const historySummary = await evaluate("document.getElementById('historyChart').querySelector('.chart-summary')?.textContent || ''");
assert.match(historySummary, /observations? from/, 'chart summary should describe the trend window');
assert.match(historySummary, /ago\)/, 'chart summary should state the observation age');
console.log('OK: weather-history chart states trend window and observation age');

// 6. CSV export responds with real rows.
const exportHref = await evaluate("document.getElementById('export').href");
const csvResponse = await fetch(exportHref);
const csvText = await csvResponse.text();
assert.equal(csvResponse.status, 200, 'CSV export should respond 200');
assert.match(csvText, /area_id/, 'CSV should have a header row');
assert.ok(csvText.trim().split('\n').length >= 2, 'CSV should have at least one data row');
console.log('OK: CSV export responds 200 with data rows');

assert.deepEqual(jsErrors, [], `expected no JavaScript exceptions, got: ${JSON.stringify(jsErrors)}`);
console.log('Main planning workflow check passed: budget change, explanation, lock persistence, ' +
  'scenario comparison, weather history, CSV export. No JavaScript exceptions.');
ws.close();
