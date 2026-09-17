// Real production UI -> proxy -> A -> official MCP. No synthetic response substitution.
// node eval/integration/browser.cjs [URL] [base|faults]
const {chromium, expect} = require('../../dashboard/node_modules/@playwright/test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');

(async () => {
  const url = process.argv[2] || 'http://127.0.0.1:3000';
  const mode = process.argv[3] || 'base';
  const output = path.resolve('private-eval/integration');
  await fs.mkdir(output,{recursive:true});
  const browser = await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL || 'msedge',headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    page.setDefaultTimeout(45000);
    const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.goto(url);
    await expect(page.getByText('API v0.4',{exact:true})).toBeVisible();
    await expect(page.getByLabel('Low recovery (%)')).toHaveValue('0');
    await expect(page.getByLabel('Point recovery (%)')).toHaveValue('0');
    await expect(page.getByLabel('High recovery (%)')).toHaveValue('100');
    const creation=page.waitForResponse(r=>r.url().endsWith('/api/audits')&&r.request().method()==='POST');
    await page.getByRole('button',{name:'Model scenario',exact:true}).click();
    assert.equal((await creation).status(),201);
    let audit=await (await creation).json();
    const initial=audit;
    assert.equal(audit.contract_version,'0.4');
    assert.equal(audit.recovery.gpu_hours.point,0);
    assert.equal(audit.recovery.gpu_hours.high,audit.eligibility.eligible_gpu_hours);
    const money=v=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',minimumFractionDigits:0,maximumFractionDigits:2}).format(v);
    const number=v=>new Intl.NumberFormat('en-US',{maximumFractionDigits:2}).format(v);
    const recovery=page.getByRole('button',{name:'Inspect recovery value and evidence'});
    await expect(recovery).toHaveText(`${money(audit.recovery.reference_usd.values.low)}–${money(audit.recovery.reference_usd.values.high)}`);
    await expect(page.getByText('Team judgment · investigate before action',{exact:true})).toBeVisible();
    await expect(page.getByText(/High bound: eligibility ceiling/)).toBeVisible();
    async function claims() {
      const event=page.waitForEvent('download');
      await page.getByRole('button',{name:'Download claims',exact:true}).click();
      const value=JSON.parse(await fs.readFile(await (await event).path(),'utf8'));
      for(const key of ['low','point','high']){
        assert.equal(value.recoverable_gpu_hours[key],audit.recovery.gpu_hours[key]);
        assert.equal(value.recoverable_usd[key],audit.recovery.reference_usd.values[key]);
      }
      assert.ok(value.notes.includes(audit.audit_id));
      return value;
    }
    async function chat(question='What could go wrong?') {
      const event=page.waitForResponse(r=>r.url().endsWith('/chat')&&r.request().method()==='POST');
      await page.getByRole('button',{name:question,exact:true}).click();
      const response=await event;
      assert.equal(response.status(),200);
      const reply=await response.json();
      assert.equal(reply.audit_id,audit.audit_id);
      assert.equal(reply.status,'ok');
      assert.ok(reply.usage.tool_calls>0&&reply.usage.tool_calls<=3);
      await expect(page.getByText(reply.answer,{exact:true})).toBeVisible();
      return reply;
    }
    const firstClaims=await claims();
    const cases=[];
    if(mode==='base') {
      await page.evaluate(()=>window.scrollTo(0,0));
      await page.screenshot({path:path.join(output,'desktop.png')});
      const baseline=page.getByLabel('Baseline eligible job');
      await expect(baseline).toBeEnabled();
      const choices=await baseline.locator('option').evaluateAll(options=>options.map(o=>o.value).filter(Boolean));
      let selected, elapsed;
      for(const id of choices){
        const detail=await (await page.request.get(url+`/api/audits/${audit.audit_id}/evidence/${id}`)).json();
        const value=Object.fromEntries(detail.observations.map(o=>[o.name,o.value]));
        if(value.walltime_sec>0&&value.gpu_count>0){selected=id;elapsed=value.walltime_sec/3600;break;}
      }
      assert.ok(selected);
      for(const item of [
        {name:'success',outcome:'replacement_success',price:'0.1',queue:'0',hours:'12',boundary:true},
        {name:'failure',outcome:'replacement_failure',price:'0.1',queue:'0',hours:'12',boundary:true},
        {name:'validation',outcome:'additional_validation',price:'0.1',queue:'0',hours:'12',boundary:true},
        {name:'loss',outcome:'replacement_success',price:'100000',queue:'0',hours:'12',boundary:true},
        {name:'unknown-price',outcome:'replacement_success',price:'',queue:'0',hours:'12',boundary:true},
        {name:'unknown-queue',outcome:'replacement_success',price:'0.1',queue:'',hours:'12',boundary:true},
        {name:'unknown-boundary',outcome:'replacement_success',price:'0.1',queue:'0',hours:'12',boundary:false},
        {name:'earlier',outcome:'replacement_success',price:'0.1',queue:'0',hours:String(elapsed/2),boundary:true},
      ]){
        await expect(baseline).toBeEnabled();
        await baseline.selectOption(selected);
        await page.getByLabel('Pilot outcome assumption').selectOption(item.outcome);
        await page.getByLabel('CPU vCPUs',{exact:true}).fill('4');
        await page.getByLabel('CPU duration (hours)',{exact:true}).fill(item.hours);
        await page.getByLabel('CPU reference USD / vCPU-hour',{exact:true}).fill(item.price);
        await page.getByLabel('Extra queue hours',{exact:true}).fill(item.queue);
        await page.getByLabel('GPU reference price includes baseline host costs').setChecked(item.boundary);
        await page.getByLabel('CPU assumptions and source').fill('Hypothetical acceptance scenario; CPU behavior and price are assumptions, not measured savings.');
        const event=page.waitForResponse(r=>r.url().endsWith('/api/audits')&&r.request().method()==='POST');
        await page.getByRole('button',{name:'Model CPU pilot',exact:true}).click();
        const response=await event;
        assert.equal(response.status(),201);
        audit=await response.json();
        const result=audit.downside.cpu_pilot;
        assert.deepEqual(audit.recovery,initial.recovery);
        await expect(page.getByTestId('cpu-cost')).toHaveText(result.added_cpu_reference_usd==null?'Unknown':money(result.added_cpu_reference_usd));
        await expect(page.getByTestId('cpu-net')).toHaveText(result.net_reference_value_usd==null?'Unknown':money(result.net_reference_value_usd));
        await expect(page.getByTestId('cpu-delay')).toHaveText(result.completion_change_hours_including_extra_queue==null?'Unknown':`${number(result.completion_change_hours_including_extra_queue)} h`);
        if(['loss','failure'].includes(item.name)) assert.ok(result.net_reference_value_usd<0);
        if(item.name==='earlier') assert.ok(result.completion_change_hours_including_extra_queue<0);
        const exported=await claims();
        assert.deepEqual(exported.recoverable_gpu_hours,firstClaims.recoverable_gpu_hours);
        cases.push(item.name);
      }
      await page.getByRole('button',{name:'Inspect CPU baseline evidence'}).click();
      await expect(page.getByText('Source and joins',{exact:true})).toBeVisible();
      await page.keyboard.press('Tab');
      assert.ok(await page.evaluate(()=>document.querySelector('dialog').contains(document.activeElement)));
      await page.keyboard.press('Escape');
      for(const question of ['Why this pilot?','Which jobs are eligible?','What are the recovery assumptions?','What could go wrong?']) await chat(question);
      await page.locator('#cpu-pilot').scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(output,'cpu-desktop.png')});
      await page.setViewportSize({width:390,height:844});
      await page.locator('#cpu-pilot').scrollIntoViewIfNeeded();
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      await page.screenshot({path:path.join(output,'cpu-mobile.png')});
      await page.getByRole('button',{name:'Inspect CPU baseline evidence'}).click();
      await expect(page.getByText('Source and joins',{exact:true})).toBeVisible();
      assert.ok(await page.getByRole('dialog').evaluate(el=>el.scrollWidth<=el.clientWidth));
      await page.getByRole('button',{name:'Close evidence'}).click();
      await page.setViewportSize({width:1440,height:1000});
    }
    const reply=await chat();
    await page.getByRole('button',{name:reply.supporting_evidence_ids[0],exact:true}).click();
    await expect(page.getByText('Source and joins',{exact:true})).toBeVisible();
    await page.getByRole('button',{name:'Close evidence'}).click();
    await page.getByText('Open optional advanced reviewer').click();
    const preserved=await claims();
    for(const fault of mode==='faults'?['unavailable','malformed','wrong-audit','hang']:['unavailable']){
      await page.getByLabel('Advanced review question').fill(fault);
      await page.getByRole('button',{name:'Ask advanced reviewer'}).click();
      await chat();
      assert.deepEqual(await claims(),preserved);
      await expect(page.locator('.question-panel.advanced').getByRole('alert')).toBeVisible({timeout:40000});
    }
    assert.deepEqual(errors,[]);
    const report={result:'PASS',mode,url,cpu_cases:cases,contract:'0.4',real_mcp:true,claims_match:true,
      human_usability:'NOT RUN',C_enhancement:'NOT ENABLED'};
    await fs.writeFile(path.join(output,`browser-${mode}.json`),JSON.stringify(report,null,2));
    await fs.writeFile(path.join(output,'final-audit.json'),JSON.stringify(audit,null,2));
    await fs.writeFile(path.join(output,'claims.json'),JSON.stringify(await claims(),null,2));
    console.log(JSON.stringify(report,null,2));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
