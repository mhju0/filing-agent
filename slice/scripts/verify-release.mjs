import { chromium } from '../../verification/node_modules/playwright/index.mjs';
import AxeBuilder from '../../verification/node_modules/@axe-core/playwright/dist/index.mjs';
import {writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const base=process.env.VERIFY_BASE||'http://127.0.0.1:4176';
const browser=await chromium.launch({channel:'chrome',headless:true});
const checks=[];
try{
 for(const lang of ['ko','en']) for(const width of [1440,390,320]){
  const context=await browser.newContext({viewport:{width,height:900},colorScheme:width===390?'dark':'light',reducedMotion:'reduce'});
  const page=await context.newPage();
  const response=await page.goto(base+'/engineering-'+lang+'.html');assert.equal(response.status(),200);
  await page.evaluate(()=>document.fonts.ready);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  const axe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  assert.deepEqual(axe.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[]);
  if(width===1440){
   await page.locator('video').evaluate(async video=>{await video.play();video.pause();if(video.error)throw Error(video.error.message)});
  }
  for(const href of await page.locator('a').evaluateAll(links=>links.map(a=>a.href))){
   const response=await page.request.get(href);assert.equal(response.status(),200,href);
  }
  await page.screenshot({path:`docs/audits/2026-09-08-slice/notes-${lang}-${width}.png`,fullPage:true});
  checks.push(lang+' '+width+' project notes: links, reflow, axe passed');await context.close();
 }
 const context=await browser.newContext();const page=await context.newPage();
 await page.route('**/recording.json',r=>r.fulfill({status:503,body:'unavailable'}));
 await page.goto(base);
 await page.getByRole('button',{name:'English',exact:true}).click();
 await page.getByText('The recording could not be loaded.',{exact:true}).waitFor();
 const reload=page.getByRole('button',{name:'Reload recording'});await reload.click();
 await page.getByText('The recording could not be loaded.',{exact:true}).waitFor();
 checks.push('Recording asset failure is visible and reload works');
 await context.close();
 await writeFile('docs/audits/2026-09-08-slice/release-browser.json',JSON.stringify({status:'PASS',base,checks},null,2)+'\n');
 console.log('RELEASE MATERIALS PASS');
}finally{await browser.close()}
