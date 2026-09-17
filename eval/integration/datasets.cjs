// Real production dataset navigation; all record-level artifacts stay private.
const {chromium, expect} = require('../../dashboard/node_modules/@playwright/test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
(async () => {
  const url = process.argv[2] || 'http://127.0.0.1:3000';
  const browser = await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL || 'msedge',headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    const get = async route => {
      const response = await page.request.get(url+route);
      assert.equal(response.status(),200);
      return response.json();
    };
    const catalog=await get('/api/datasets/catalog');
    assert.equal(catalog.synthetic,false);
    assert.ok(catalog.collections.every(c=>c.available && c.count>0));
    const version=encodeURIComponent(catalog.version);
    for(const collection of ['jobs','gpus','machines','findings']) {
      const result=await get(`/api/datasets/${collection}?version=${version}&offset=0&limit=20`);
      assert.equal(result.items.length,20);
      assert.equal(result.total,catalog.collections.find(c=>c.key===collection).count);
      const detail=await get(`/api/datasets/${collection}/${encodeURIComponent(result.items[0].id)}?version=${version}`);
      assert.equal(detail.record.id,result.items[0].id);
    }
    assert.equal((await page.request.get(url+'/api/datasets/jobs?version=stale')).status(),409);
    assert.equal((await page.request.post(url+'/api/datasets/catalog',{data:{}})).status(),405);
    assert.equal((await page.request.post(url+'/api/optimizations',{data:{}})).status(),501);
    assert.equal((await page.request.get(url+`/api/datasets/jobs?version=${version}&limit=101`)).status(),422);
    await page.goto(url+'/#data');
    await expect(page.getByRole('region',{name:'Jobs results'})).toBeVisible();
    await page.getByRole('button',{name:/^Open Job /}).first().click();
    await expect(page.getByText('Real source record',{exact:true})).toBeVisible();
    await page.keyboard.press('Escape');
    await page.getByRole('link',{name:/^GPUs /}).click();
    await expect(page.getByRole('region',{name:'GPUs results'})).toBeVisible();
    await page.getByRole('button',{name:'Next',exact:true}).click();
    await expect(page.getByText(/^21–40 of /)).toBeVisible();
    await page.getByRole('link',{name:'Decisions',exact:true}).click();
    await expect(page.getByRole('table')).toBeVisible();
    await expect(page.getByRole('row')).toHaveCount(9);
    const cpu=page.getByRole('checkbox',{name:'Select CPU placement pilot',exact:true});
    await cpu.focus(); await page.keyboard.press('Space');
    await page.getByRole('checkbox',{name:'Select Idle interactive sessions',exact:true}).check();
    await page.getByRole('button',{name:'Review selected',exact:true}).click();
    await expect(page.getByRole('button',{name:'Multi-fix modeling not yet available',exact:true})).toBeDisabled();
    const table=await get(`/api/datasets/decisions?version=${version}&selection=cpu-placement,idle-sessions`);
    assert.ok(table.selection.overlapping_gpu_hours>0);
    await expect(page.getByRole('dialog').getByText(`${table.selection.share_pct.toFixed(1)}%`,{exact:true})).toBeVisible();
    await page.getByRole('button',{name:'Return',exact:true}).click();
    await fs.mkdir('private-eval/integration',{recursive:true});
    await page.screenshot({path:'private-eval/integration/decisions-production.png',fullPage:true});
    await page.getByRole('row').filter({has:cpu}).getByRole('link').click();
    await expect(page.getByLabel('Search findings')).toHaveValue('rules::gpu-not-needed');
    await expect(page.getByRole('cell',{name:'rules::gpu-not-needed',exact:true}).first()).toBeVisible();
    await page.getByRole('button',{name:/^Open /}).first().click();
    await expect(page.getByText('Source-derived finding',{exact:true})).toBeVisible();
    await page.getByRole('dialog').getByRole('button',{name:/^Job /}).first().click();
    await expect(page.getByText('Real source record',{exact:true})).toBeVisible();
    await page.keyboard.press('Escape');
    await page.setViewportSize({width:390,height:844});
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.getByRole('link',{name:'Decisions',exact:true}).click();
    await expect(page.getByRole('table')).toBeVisible();
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.screenshot({path:'private-eval/integration/decisions-production-mobile.png',fullPage:true});
    assert.deepEqual(errors,[]);
    console.log(JSON.stringify({result:'PASS',url,collections:4,read_only:true,decisions:'real observed exposure',multi_fix:'disabled',desktop_mobile:true}));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1});
