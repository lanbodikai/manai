// Real organizer-data acceptance. Run only against the isolated Compose project.
const {chromium, expect} = require('../../dashboard/node_modules/@playwright/test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {execFileSync} = require('node:child_process');

(async () => {
  const [url, output] = process.argv.slice(2);
  const root = path.resolve(__dirname, '../..');
  const compose = ['compose','-p','manai-c-smoke','-f','docker-compose.yml','-f','reviewer/compose.integration.yml','-f','reviewer/.private/real-host-pass/host-smoke.yml','--profile','reviewer'];
  const docker = (...args) => execFileSync(process.env.DOCKER_BIN || 'docker', args, {cwd:root,env:process.env,timeout:120000,encoding:'utf8'});
  const save = (name, data) => fs.writeFile(path.join(output,name), JSON.stringify(data,null,2), {mode:0o600});
  const browser = await chromium.launch({channel:'chrome',headless:true});
  const receipt = {started:new Date().toISOString(),checks:[],provider_calls:0};
  let stopped = false;
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    page.setDefaultTimeout(45000);
    const errors=[];
    page.on('pageerror', e=>errors.push(e.message));
    await page.goto(url);
    await expect(page.getByText('API v0.4',{exact:true})).toBeVisible();
    async function create(button) {
      const pending=page.waitForResponse(r=>r.url().endsWith('/api/audits')&&r.request().method()==='POST');
      await page.getByRole('button',{name:button,exact:true}).click();
      const response=await pending;
      assert.equal(response.status(),201);
      return response.json();
    }
    let audit=await create('Model scenario');
    assert.equal(audit.provenance.synthetic,false);
    receipt.baseline_audit_id=audit.audit_id;
    await save('baseline-audit.json',audit);
    async function claims(name) {
      const pending=page.waitForEvent('download');
      await page.getByRole('button',{name:'Download claims',exact:true}).click();
      const value=JSON.parse(await fs.readFile(await (await pending).path(),'utf8'));
      assert.ok(value.notes.includes(audit.audit_id));
      if(name) await save(name,value);
      return value;
    }
    await claims('baseline-claims.json');
    await expect(page.getByLabel('Baseline eligible job')).toBeEnabled();
    const ids=await page.getByLabel('Baseline eligible job').locator('option').evaluateAll(options=>options.map(o=>o.value).filter(Boolean));
    let selected;
    for(const id of ids) {
      const response=await page.request.get(url+`/api/audits/${audit.audit_id}/evidence/${encodeURIComponent(id)}`);
      assert.equal(response.status(),200);
      const detail=await response.json();
      const values=Object.fromEntries(detail.observations.map(o=>[o.column,o.value]));
      if(values.gpu_count>0 && values.walltime_sec>0) {selected=id;await save('selected-evidence.json',detail);break;}
    }
    assert.ok(selected,'No valid positive-duration GPU baseline');
    await page.getByLabel('Baseline eligible job').selectOption(selected);
    await page.getByLabel('Pilot outcome assumption').selectOption('replacement_failure');
    for(const [label,value] of [['CPU vCPUs','1'],['CPU duration (hours)','0.5'],['CPU reference USD / vCPU-hour','0.10'],['Extra queue hours','0'],['Assumed trial cap (hours)','0.5']]) await page.getByLabel(label,{exact:true}).fill(value);
    await page.getByLabel('GPU reference price includes baseline host costs').check();
    await page.getByLabel('CPU assumptions and source').fill('Hypothetical failed CPU trial followed by a full GPU rerun. CPU allocation, runtime, rate, queue delay, trial cap and inclusion of baseline host costs are assumptions. No workload executed.');
    const recovery=audit.recovery;
    audit=await create('Model CPU pilot');
    receipt.audit_id=audit.audit_id;
    await save('pilot-audit.json',audit);
    assert.deepEqual(audit.recovery,recovery);
    const p=audit.downside.cpu_pilot;
    assert.equal(p.added_cpu_reference_usd,0.05);
    assert.equal(p.net_reference_value_usd,-0.05);
    assert.equal(p.released_gpu_hours,0);
    // Real telemetry preserves recorded allocation H separately from g*T.
    assert.equal(p.scenario_gpu_hours,p.baseline.recorded_gpu_hours);
    assert.equal(p.completion_change_hours_including_extra_queue,0.5);
    receipt.checks.push('failed CPU trial adds $0.05; one full GPU rerun; cohort recovery unchanged');
    const preserved=await claims('pilot-claims.json');
    await page.getByText('Open optional advanced reviewer').click();
    async function review(button='Ask advanced reviewer') {
      const pending=page.waitForResponse(r=>r.url().endsWith('/explanations')&&r.request().method()==='POST');
      await page.getByRole('button',{name:button,exact:true}).click();
      return pending;
    }
    await page.getByLabel('Advanced review question').fill('Review the failed CPU trial, full GPU rerun, cost, evidence coverage and recovery assumptions.');
    let response=await review();
    assert.equal(response.status(),200);
    const result=await response.json();
    await save('website-review.json',result);
    assert.equal(result.audit_id,audit.audit_id);
    assert.equal(result.client_request_id,response.request().postDataJSON().client_request_id);
    assert.equal(result.usage.provider,null);
    assert.match(result.answer,/Independent checks: \d+ PASS, 0 FAIL, \d+ UNKNOWN/);
    await expect(page.locator('.question-panel.advanced').getByText(result.answer,{exact:true})).toBeVisible();
    async function evidence() {
      await page.getByRole('button',{name:'Inspect CPU baseline evidence'}).click();
      await expect(page.getByText('Source and joins',{exact:true})).toBeVisible();
      await page.getByRole('button',{name:'Close evidence'}).click();
    }
    await page.locator('.question-panel.advanced .citations button').first().click();
    await expect(page.getByText('Source and joins',{exact:true})).toBeVisible();
    await page.getByRole('button',{name:'Close evidence'}).click();
    assert.deepEqual(await claims(),preserved);
    assert.deepEqual(await (await page.request.get(url+`/api/audits/${audit.audit_id}`)).json(),audit);
    receipt.checks.push('website review identity, citation drawer, audit and claims preserved');
    await page.locator('.question-panel.advanced .answer').evaluate(el=>el.scrollIntoView({block:'start'}));
    await page.screenshot({path:path.join(output,'review-desktop.png')});
    await page.setViewportSize({width:390,height:844});
    await page.locator('.question-panel.advanced .answer').evaluate(el=>el.scrollIntoView({block:'start'}));
    await page.screenshot({path:path.join(output,'review-mobile.png')});
    const dimensions=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
    assert.ok(dimensions.scroll<=dimensions.width,JSON.stringify(dimensions));
    receipt.checks.push('390px review layout has no horizontal overflow');
    await page.setViewportSize({width:1440,height:1000});
    const live=docker(...compose,'run','--rm','--no-deps','--user','0:0','-v',`${root}/eval:/app/eval:ro`,'-v',`${output}:/receipts`,'reviewer','python','-m','eval.agent.live_review','--analysis-url','http://analysis:8001','--reviewer-url','http://reviewer:8002','--explanations-url','http://dashboard:3000','--audit-id',audit.audit_id,'--output','/receipts/live-review.json');
    await fs.writeFile(path.join(output,'live-review.log'),live);
    receipt.checks.push('one-off container live review through dashboard proxy');
    docker(...compose,'stop','reviewer');stopped=true;
    response=await review();
    assert.equal(response.status(),503);
    await expect(page.locator('.question-panel.advanced').getByRole('alert')).toBeVisible();
    const chatPending=page.waitForResponse(r=>r.url().endsWith('/chat')&&r.request().method()==='POST');
    await page.getByRole('button',{name:'What could go wrong?',exact:true}).click();
    const chat=await chatPending;
    assert.equal(chat.status(),200);
    const chatBody=await chat.json();
    assert.equal(chatBody.usage.tool_calls,2);
    assert.equal(chatBody.audit_id,audit.audit_id);
    await save('base-chat-while-c-stopped.json',chatBody);
    await evidence();
    assert.deepEqual(await claims(),preserved);
    assert.deepEqual(await (await page.request.get(url+`/api/audits/${audit.audit_id}`)).json(),audit);
    await page.locator('#ask').scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(output,'review-unavailable.png')});
    receipt.checks.push('C stopped: visible 503; base MCP chat, evidence, audit and claims preserved');
    docker(...compose,'up','-d','--no-deps','--no-build','--wait','--wait-timeout','60','reviewer');stopped=false;
    response=await review('Retry question');
    assert.equal(response.status(),200);
    const retried=await response.json();
    assert.equal(retried.audit_id,audit.audit_id);
    await expect(page.locator('.question-panel.advanced').getByText(retried.answer,{exact:true})).toBeVisible();
    receipt.checks.push('C restart and visible website retry succeeded');
    assert.deepEqual(errors,[]);
    receipt.result='PASS';
  } catch(error) {
    receipt.result='FAIL';receipt.error=String(error.stack||error);
    // Leave optional C disabled after any failed acceptance check.
    if(!stopped) {docker(...compose,'stop','reviewer');stopped=true;}
    process.exitCode=1;
  } finally {
    receipt.completed=new Date().toISOString();receipt.reviewer_disabled=stopped;
    await save('browser-receipt.json',receipt);
    console.log(JSON.stringify(receipt,null,2));
    await browser.close();
  }
})();
