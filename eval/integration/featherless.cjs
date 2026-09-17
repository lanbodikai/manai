const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require('../../dashboard/node_modules/playwright');
const base=process.argv[2]||'http://127.0.0.1:13121';
const output=path.resolve('private-eval/featherless-'+Date.now());fs.mkdirSync(output,{recursive:true});
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  await page.goto(base+'/#ask');
  await page.getByRole('button',{name:'Trace this cost estimate back to its evidence.'}).waitFor({timeout:60000});
  const response=page.waitForResponse(r=>r.url().endsWith('/review'),{timeout:35000});
  await page.getByRole('button',{name:'Trace this cost estimate back to its evidence.'}).click();
  const http=await response,result=await http.json();
  fs.writeFileSync(path.join(output,'review.json'),JSON.stringify(result,null,2));
  if(http.status()!==200)throw Error(JSON.stringify(result));
  if(result.usage.provider!=='Featherless'||!result.usage.model||result.usage.tool_calls!==1)throw Error('Missing actual model/MCP usage');
  if(result.checks.some(c=>c.status==='fail'))throw Error('Failed arithmetic/price check');
  if(!result.checks.some(c=>c.status==='unknown')||result.status!=='insufficient_evidence')throw Error('Uncertainty suppressed');
  await page.getByText('Featherless-assisted review',{exact:true}).waitFor();
  await page.screenshot({path:path.join(output,'desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2))throw Error('Mobile overflow');
  await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
  await page.getByRole('button',{name:'Base pilot assistant',exact:true}).click();
  await page.getByRole('button',{name:'Why this pilot?',exact:true}).click();
  await page.locator('.assistant-text').filter({hasText:'MCP evidence chatbot'}).waitFor({timeout:15000});
  console.log(JSON.stringify({status:'PASS',model:result.usage.model,checks:result.checks.length,failures:0,coverage:result.coverage,receipt:output}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
