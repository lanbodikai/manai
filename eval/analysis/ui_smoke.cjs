// Live integration witness against an unchanged B review copy; no UI source edits.
// Usage: node ui_smoke.cjs <B dashboard node_modules> [UI URL]
const { chromium, expect } = require(require('node:path').resolve(process.argv[2], '@playwright/test'));
const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');

(async () => {
  const output = path.resolve('private-eval/ui');
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    page.setDefaultTimeout(45000);
    const errors = [], requests = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('request', r => requests.push(r.url()));
    await page.goto(process.argv[3] || 'http://127.0.0.1:13000');
    await page.getByLabel('Low recovery (%)').fill('0');
    await page.getByLabel('Point recovery (%)').fill('0');
    await page.getByLabel('High recovery (%)').fill('100');
    await page.getByLabel('Reference $ / GPU-hour').fill('2.5');
    await page.getByLabel('Why these assumptions?').fill('No empirical CPU recoverability: zero low/point; high is the eligibility ceiling, not a forecast.');
    const creation = page.waitForResponse(r => r.url().endsWith('/api/audits') && r.request().method() === 'POST');
    await page.getByRole('button', { name: 'Model scenario' }).click();
    const created = await creation;
    assert.equal(created.status(), 201);
    const audit = await created.json();
    const usd = v => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(v);
    const recovery = page.getByRole('button', { name: 'Inspect recovery value and evidence' });
    await expect(recovery).toHaveText(`${usd(audit.recovery.reference_usd.values.low)}–${usd(audit.recovery.reference_usd.values.high)}`);
    const downloadClaims = async () => {
      const event = page.waitForEvent('download');
      await page.getByRole('button', { name: 'Download claims', exact: true }).click();
      const download = await event;
      const claims = JSON.parse(await fs.readFile(await download.path(), 'utf8'));
      assert.equal(claims.recoverable_gpu_hours.point, audit.recovery.gpu_hours.point);
      assert.equal(claims.recoverable_gpu_hours.high, audit.recovery.gpu_hours.high);
      assert.equal(claims.recoverable_usd.high, audit.recovery.reference_usd.values.high);
      assert.ok(claims.notes.includes(audit.audit_id));
      return claims;
    };
    const claims = await downloadClaims();
    const ask = async () => {
      const event = page.waitForResponse(r => r.url().endsWith('/chat') && r.request().method() === 'POST');
      await page.getByRole('button', { name: 'What could go wrong?', exact: true }).click();
      const response = await event;
      assert.equal(response.status(), 200);
      const reply = await response.json();
      assert.equal(reply.status, 'ok');
      assert.equal(reply.audit_id, audit.audit_id);
      assert.ok(reply.usage.tool_calls > 0 && reply.usage.tool_calls <= 3);
      await expect(page.getByText(reply.answer, { exact: true })).toBeVisible();
      return reply;
    };
    const answer = await ask();
    await page.getByRole('button', { name: answer.supporting_evidence_ids[0], exact: true }).click();
    await expect(page.getByText('Source and joins')).toBeVisible();
    await page.getByRole('button', { name: 'Close evidence' }).click();
    await page.screenshot({ path: path.join(output, 'desktop.png'), fullPage: true });
    await page.getByText('Open optional advanced reviewer').click();
    await page.getByLabel('Advanced review question').fill('Why this pilot?');
    const failureResults = [];
    for (const mode of ['unavailable', 'malformed', 'wrong-audit', 'hang']) {
      await page.route('**/explanations', route => {
        if (mode === 'hang') return;
        if (mode === 'unavailable') return route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({error: { code: 'AGENT_UNAVAILABLE', message: 'Optional reviewer unavailable', retryable: true, request_id: 'ui-witness' }}) });
        return route.fulfill({ status: 200, contentType: 'application/json', body: mode === 'malformed' ? '{broken' : JSON.stringify({ ...answer, audit_id: 'wrong-audit', client_request_id: JSON.parse(route.request().postData()).client_request_id }) });
      });
      await page.getByRole('button', { name: 'Ask advanced reviewer' }).click();
      // During optional failure/hang, base chat and export still make real A calls.
      await ask();
      const nextClaims = await downloadClaims();
      assert.deepEqual(nextClaims, claims);
      await expect(page.getByRole('alert')).toBeVisible({ timeout: 40000 });
      failureResults.push(mode);
      await page.unroute('**/explanations');
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(recovery).toBeVisible();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: path.join(output, 'mobile.png'), fullPage: true });
    assert.equal(requests.some(u => /\/src\/mock\//.test(u)), false);
    assert.deepEqual(errors, []);
    const result = { result: 'PASS', frontend: 'unchanged B at 5a8d995', mode: 'real HTTP', audit_id: audit.audit_id,
      M01: 'PASS live UI -> A -> official MCP with resolving citation', M04: 'PASS preview failure injection; base chat/export survive optional unavailable/malformed/wrong-audit/hang',
      C04: 'displayed audit matches downloaded claims', D06: '0/0/1 displayed/export agreement; final REPORT remains B-owned',
      failure_modes: failureResults, no_mock_modules: true, no_page_errors: true,
      limitations: ['Development preview, not final Compose/P01 or independent human U05', 'R05 optional image build failure not tested'] };
    await fs.writeFile(path.join(output, 'results.json'), JSON.stringify(result, null, 2));
    console.log(JSON.stringify(result, null, 2));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
