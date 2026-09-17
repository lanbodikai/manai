// Production UI with actual A/C/API/MCP over explicitly invented on-disk data.
const {chromium, expect} = require('../../dashboard/node_modules/@playwright/test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');

(async () => {
  const [url, mode, output] = process.argv.slice(2);
  const browser = await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL || 'chrome',headless:true});
  const checks=[], errors=[];
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    page.setDefaultTimeout(45000);
    page.on('pageerror', e=>errors.push(e.message));
    await page.goto(url);
    await expect(page.getByText('API v0.4',{exact:true})).toBeVisible();
    const creation=page.waitForResponse(r=>r.url().endsWith('/api/audits')&&r.request().method()==='POST');
    await page.getByRole('button',{name:'Model scenario',exact:true}).click();
    const created=await creation;
    assert.equal(created.status(),201);
    let audit=await created.json();
    assert.equal(audit.provenance.synthetic,true);
    assert.equal(audit.eligibility.unique_jobs,2);
    assert.equal(audit.eligibility.eligible_gpu_hours,30);
    const originalRecovery=audit.recovery;
    checks.push('production UI created synthetic-labelled audit');
    async function claims() {
      const event=page.waitForEvent('download');
      await page.getByRole('button',{name:'Download claims',exact:true}).click();
      const result=JSON.parse(await fs.readFile(await (await event).path(),'utf8'));
      for(const key of ['low','point','high']){
        assert.equal(result.recoverable_gpu_hours[key],audit.recovery.gpu_hours[key]);
        assert.equal(result.recoverable_usd[key],audit.recovery.reference_usd.values[key]);
      }
      assert.ok(result.notes.includes(audit.audit_id));
      return result;
    }
    async function chat(question='What could go wrong?') {
      const event=page.waitForResponse(r=>r.url().endsWith('/chat')&&r.request().method()==='POST');
      await page.getByRole('button',{name:question,exact:true}).click();
      const response=await event;
      assert.equal(response.status(),200);
      const result=await response.json();
      assert.equal(result.audit_id,audit.audit_id);
      assert.equal(result.status,'ok');
      assert.equal(result.usage.tool_calls,2);
      assert.equal(result.usage.provider,null);
      await expect(page.getByText(result.answer,{exact:true})).toBeVisible();
      return result;
    }
    async function verifyReview() {
      if(await page.locator('.reviewer-disclosure').getAttribute('open')===null) await page.getByText('Open optional advanced reviewer').click();
      const before=await claims();
      const event=page.waitForResponse(r=>r.url().endsWith('/explanations')&&r.request().method()==='POST');
      await page.getByLabel('Advanced review question').fill('Review calculation, cost, risk and recovery');
      await page.getByRole('button',{name:'Ask advanced reviewer'}).click();
      const response=await event;
      assert.equal(response.status(),200);
      const result=await response.json();
      assert.equal(result.audit_id,audit.audit_id);
      assert.equal(result.client_request_id,response.request().postDataJSON().client_request_id);
      assert.equal(result.status,'insufficient_evidence');
      assert.equal(result.usage.provider,null);
      assert.equal(result.usage.tool_calls,2);
      assert.match(result.answer,/Independent checks: \d+ PASS, 0 FAIL, \d+ UNKNOWN/);
      await expect(page.locator('.question-panel.advanced').getByText(result.answer,{exact:true})).toBeVisible();
      for(const id of result.supporting_evidence_ids){
        const detail=await page.request.get(url+`/api/audits/${audit.audit_id}/evidence/${id}`);
        assert.equal(detail.status(),200);
        assert.equal((await detail.json()).audit_id,audit.audit_id);
      }
      const citation=page.locator('.question-panel.advanced .citations button').first();
      await citation.click();
      await expect(page.getByText('Source and joins',{exact:true})).toBeVisible();
      await page.getByRole('button',{name:'Close evidence'}).click();
      assert.deepEqual(await claims(),before);
      const canonical=await (await page.request.get(url+`/api/audits/${audit.audit_id}`)).json();
      assert.deepEqual(canonical,audit);
    }
    await chat();
    await page.getByText('Open optional advanced reviewer').click();
    let reviews=0;
    if(mode==='full') {
      await verifyReview(); reviews++;
      const evidence=await (await page.request.get(url+`/api/audits/${audit.audit_id}/evidence?limit=100`)).json();
      const selected=evidence.items.find(e=>e.kind==='job'&&e.source_id==='J2').id;
      const cases=JSON.parse(await fs.readFile(path.join(__dirname,'../../contracts/examples/pilot-cases.json'),'utf8'));
      const money=v=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',minimumFractionDigits:0,maximumFractionDigits:2}).format(v);
      for(const item of cases) {
        const input=item.input;
        await page.getByLabel('Baseline eligible job').selectOption(selected);
        await page.getByLabel('Pilot outcome assumption').selectOption(input.mode);
        await page.getByLabel('CPU vCPUs',{exact:true}).fill(String(input.cpu_vcpus));
        await page.getByLabel('CPU duration (hours)',{exact:true}).fill(String(input.cpu_hours));
        await page.getByLabel('CPU reference USD / vCPU-hour',{exact:true}).fill(input.cpu_vcpu_hour_usd==null?'':String(input.cpu_vcpu_hour_usd));
        await page.getByLabel('Extra queue hours',{exact:true}).fill(input.extra_queue_hours==null?'':String(input.extra_queue_hours));
        await page.getByLabel('Assumed trial cap (hours)',{exact:true}).fill(input.trial_cap_hours==null?'':String(input.trial_cap_hours));
        await page.getByLabel('GPU reference price includes baseline host costs').setChecked(input.baseline_host_costs_included);
        await page.getByLabel('CPU assumptions and source').fill(input.assumption_note);
        const event=page.waitForResponse(r=>r.url().endsWith('/api/audits')&&r.request().method()==='POST');
        await page.getByRole('button',{name:'Model CPU pilot',exact:true}).click();
        const response=await event;
        assert.equal(response.status(),201);
        audit=await response.json();
        assert.deepEqual(audit.recovery,originalRecovery);
        for(const field of ['released_gpu_hours','scenario_gpu_hours','added_cpu_vcpu_hours','added_cpu_reference_usd','net_reference_value_usd','run_time_change_hours_excluding_queue','completion_change_hours_including_extra_queue']){
          const actual=audit.downside.cpu_pilot[field],expected=item.result[field];
          if(expected==null) assert.equal(actual,null); else assert.ok(Math.abs(actual-expected)<1e-8,`${item.name}: ${field}: ${actual} vs ${expected}`);
        }
        await expect(page.getByTestId('cpu-net')).toHaveText(item.result.net_reference_value_usd==null?'Unknown':money(item.result.net_reference_value_usd));
        await verifyReview(); reviews++;
        checks.push(item.name+' UI/A/C calculation, citations and export');
      }
      for(const q of ['Why this pilot?','Which jobs are eligible?','What are the recovery assumptions?']) await chat(q);
      await page.locator('#ask').scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(output,'review-desktop.png')});
      await page.setViewportSize({width:390,height:844});
      await page.locator('#ask').scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(output,'review-mobile.png')});
      const overflow=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,
        elements:[...document.querySelectorAll('body *')].filter(el=>el.getBoundingClientRect().right>innerWidth).map(el=>({tag:el.tagName,cls:el.className,right:el.getBoundingClientRect().right,text:el.textContent.slice(0,90)})).slice(0,12)}));
      await fs.writeFile(path.join(output,'mobile-layout.json'),JSON.stringify(overflow,null,2));
      assert.ok(overflow.scroll<=overflow.width,JSON.stringify(overflow));
      checks.push('real base MCP chat and narrow layout');
    } else {
      const preserved=await claims();
      for(const fault of mode==='faults'?['unavailable','malformed','wrong-audit','hang']:['unavailable']) {
        await page.getByLabel('Advanced review question').fill(fault);
        const started=Date.now();
        await page.getByRole('button',{name:'Ask advanced reviewer'}).click();
        await chat();
        assert.deepEqual(await claims(),preserved);
        await expect(page.locator('.question-panel.advanced').getByRole('alert')).toBeVisible({timeout:40000});
        if(fault==='hang') assert.ok(Date.now()-started>=30000&&Date.now()-started<39000);
        assert.equal(await page.locator('.question-panel.advanced .answer').count(),0);
        const retry=page.locator('.question-panel.advanced').getByRole('button',{name:'Retry question'});
        await expect(retry).toBeEnabled();
        if(fault==='unavailable') {
          await retry.click();
          await expect(page.locator('.question-panel.advanced').getByRole('alert')).toBeVisible();
        }
        checks.push(mode+': '+fault+' isolated; actual base MCP and export preserved');
      }
      await page.locator('#ask').scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(output,mode+'-error.png')});
    }
    assert.deepEqual(errors,[]);
    await fs.writeFile(path.join(output,mode+'-claims.json'),JSON.stringify(await claims(),null,2));
    console.log(JSON.stringify({result:'PASS',mode,reviews,checks,source:'Original synthetic disk bundle; actual API/A/C/MCP/proxy/UI; provenance-only A wrapper',provider_calls:0}));
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
