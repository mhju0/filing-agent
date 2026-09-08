import { chromium } from '../../verification/node_modules/playwright/index.mjs';
import { writeFile } from 'node:fs/promises';
const out='docs/audits/2026-09-08-slice';
const browser=await chromium.launch({channel:'chrome',headless:true});
const context=await browser.newContext({viewport:{width:1280,height:900},recordVideo:{dir:'.local/video',size:{width:1280,height:900}},reducedMotion:'reduce'});
const page=await context.newPage();
await page.goto('http://127.0.0.1:8765');
await page.getByRole('textbox').waitFor();
await page.getByRole('button',{name:'English',exact:true}).click();
for(const q of ['삼성전자 2023년 매출액은?','네이버는?']){
 await page.getByRole('textbox').fill(q);
 await page.getByRole('button',{name:'Ask',exact:true}).click();
 await page.locator('article').last().locator('.figure').waitFor({timeout:120000});
 await page.getByRole('button',{name:'Save investigation',exact:true}).waitFor();
 await page.locator('article').last().locator('.figure').click();
 await page.waitForTimeout(2500);
}
await page.getByRole('button',{name:'Save investigation',exact:true}).click();
await page.getByRole('button',{name:'Continue with original evidence',exact:true}).waitFor();
const id=await page.evaluate(()=>localStorage.getItem('filing-investigation'));
const response=await page.request.get('http://127.0.0.1:8765/api/investigations/'+id);
await writeFile(out+'/actual-run.json',JSON.stringify({kind:'Unedited browser capture, actual local inference',investigation:await response.json()},null,2)+'\n');
await context.close();
await page.video().saveAs(out+'/actual-run.webm');
await browser.close();
console.log('ACTUAL VIDEO CAPTURED');
