// Live Decisions selection must feed simulation, never workload execution.
const {chromium,expect}=require('../../dashboard/node_modules/@playwright/test');
const assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({channel:'msedge',headless:true});try{
 const page=await browser.newPage();
 let executionRequests=0;
 page.on('request',r=>{if(r.url().endsWith('/api/optimizations')&&r.method()==='POST')executionRequests++;});
 await page.goto((process.argv[2]||'http://127.0.0.1:13121')+'/#optimization');
 const boxes=page.locator('.decision-table tbody input[type=checkbox]');
 await expect(boxes).toHaveCount(8);
 for(let i=0;i<8;i++)await expect(boxes.nth(i)).toBeEnabled();
 await page.getByRole('checkbox',{name:'Select all available fixes'}).check();
 await expect(page.getByText('8 actions selected',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Clear selection',exact:true}).click();
 await expect(page.getByRole('button',{name:'Model selected tasks',exact:true})).toBeDisabled();
 await boxes.nth(0).check();await boxes.nth(1).check();
 await page.getByRole('button',{name:'Model selected tasks',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Cost-reduction simulation'})).toBeVisible();
 await expect(page.locator('.portfolio-action input[type=checkbox]:checked')).toHaveCount(2);
 const response=page.waitForResponse(r=>r.url().endsWith('/api/portfolio-simulations')&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Recalculate',exact:true}).click();
 const http=await response;assert.equal(http.status(),201);
 const result=await http.json();assert.equal(result.actions.length,2);
 assert.equal(executionRequests,0);
 console.log('PASS: eight tasks selectable; select-all/clear; selected pair carried into Model and recalculated; no execution request.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
