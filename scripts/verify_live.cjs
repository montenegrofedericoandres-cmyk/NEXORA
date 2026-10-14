// Check the public deployment without authentication or paid services.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium, request} = require('playwright');
const url = new URL('https://nexora.nexoraproductosdigitales.workers.dev/');
const expected = fs.readFileSync(path.resolve(__dirname,'../index.html'),'utf8');
const privatePaths = ['.git/HEAD','.git/config','.github/workflows/quality.yml','.env','README.md','scripts/build_site.py','docs/ARQUITECTURA_AUTOMATIZACION.md','wrangler.jsonc','.assetsignore','producto.xlsx'];

(async () => {
  const client = await request.newContext({timeout:15000});
  let ready = false;
  try {
    for (let attempt=1; attempt<=12 && !ready; attempt++) {
      try {
        const home = await client.get(url.href);
        assert.equal(home.status(),200,'Public homepage must return 200');
        assert.equal(await home.text(),expected,'Published page must match main');
        const headers = home.headers();
        assert.ok(headers['content-security-policy']?.includes("form-action 'none'"),'Checkout form protection missing');
        assert.ok(headers['content-security-policy']?.includes("default-src 'none'"),'External script protection missing');
        assert.equal(headers['x-content-type-options'],'nosniff');
        assert.equal(headers['x-frame-options'],'DENY');
        for (const pathname of privatePaths) {
          const response = await client.get(new URL(pathname,url).href);
          // Do not print or inspect response bodies for private paths.
          assert.equal(response.status(),404,'Internal/product path must return 404: '+pathname);
          await response.dispose();
        }
        ready = true;
        console.log('PASS: HTTPS, published HTML, security headers, and '+privatePaths.length+' blocked internal/product paths');
      } catch(error) {
        if(attempt===12) throw error;
        console.log('Waiting for Cloudflare deployment: attempt '+attempt+'/12; '+error.message.split('\n')[0]);
        await new Promise(resolve=>setTimeout(resolve,5000));
      }
    }
  } finally { await client.dispose(); }
  let browser;
  try {
    browser = await chromium.launch({headless:true});
    for(const width of [320,360,390,412,768,1280]) {
      const page = await browser.newPage({viewport:{width,height:900},hasTouch:width<768,isMobile:width<768});
      const errors = [];
      page.on('pageerror',error=>errors.push(error.message));
      assert.equal((await page.goto(url.href)).status(),200);
      const state = await page.evaluate(()=>({
        viewport:innerWidth,
        documentWidth:document.documentElement.scrollWidth,
        overflow:[...document.querySelectorAll('body *')].filter(element=>{const r=element.getBoundingClientRect();return r.width&&(r.left < -1 || r.right>innerWidth+1);}).map(element=>element.tagName),
        prelaunch:document.body.textContent.includes('Próximamente disponible.'),
        contactHeight:document.querySelector('.contact')?.getBoundingClientRect().height,
        forms:document.forms.length,
        scripts:document.scripts.length,
        downloads:document.querySelectorAll('[download]').length,
        links:[...document.querySelectorAll('a')].map(element=>element.getAttribute('href'))
      }));
      console.log(JSON.stringify({live:true,width,...state,errors}));
      assert.equal(state.viewport,width);
      assert.equal(state.documentWidth,width);
      assert.deepEqual(state.overflow,[]);
      assert.deepEqual(errors,[]);
      assert.ok(state.prelaunch && state.contactHeight>=44);
      assert.equal(state.forms+state.scripts+state.downloads,0);
      assert.ok(state.links.length && state.links.every(href=>href.startsWith('mailto:nexoraproductosdigitales@gmail.com')));
      await page.close();
    }
    console.log('PASS: public deployment at six mobile/tablet/desktop viewports; payments and digital deliveries disabled');
  } finally { await browser?.close(); }
})().catch(error=>{console.error(error.message);process.exitCode=1;});
