// Check the public deployment without authentication or paid services.
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const url = new URL('https://nexora.nexoraproductosdigitales.workers.dev/');
const privatePaths = ['.git/HEAD','.git/config','.github/workflows/quality.yml','.env','README.md','scripts/build_site.py','docs/ARQUITECTURA_AUTOMATIZACION.md','wrangler.jsonc','.assetsignore','producto.xlsx'];
const securityHeaders = {
  'content-security-policy': "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
  'x-content-type-options': 'nosniff',
  'x-frame-options': 'DENY',
  'referrer-policy': 'no-referrer',
  'permissions-policy': 'camera=(), microphone=(), geolocation=()'
};
const digest = value => createHash('sha256').update(value).digest('hex');

async function verifyHttp({expectedHtml, baseUrl=url, fetchImpl=globalThis.fetch}) {
  assert.equal(baseUrl.protocol,'https:','Public deployment must use HTTPS');
  // One deadline covers the homepage and all private paths in this attempt.
  const options = {redirect:'manual', signal:AbortSignal.timeout(30000)};
  const home = await fetchImpl(baseUrl.href,options);
  try {
    assert.equal(home.status,200,'Public homepage must return 200');
    for (const [name,value] of Object.entries(securityHeaders)) {
      assert.equal(home.headers.get(name),value,'Security header mismatch: '+name);
    }
    // Compare hashes so a mismatch never prints the response body in CI logs.
    assert.equal(digest(await home.text()),digest(expectedHtml),'Published page must match main');
  } finally {
    if (!home.bodyUsed) await home.body?.cancel();
  }
  for (const pathname of privatePaths) {
    const response = await fetchImpl(new URL(pathname,baseUrl).href,options);
    try {
      assert.equal(response.status,404,'Internal/product path must return 404: '+pathname);
    } finally {
      // Never read or print bodies for internal/product paths, even on failure.
      await response.body?.cancel();
    }
  }
}

async function main() {
  const args = process.argv.slice(2);
  assert.ok(args.length===0 || (args.length===1 && args[0]==='--http-only'),'Usage: node scripts/verify_live.cjs [--http-only]');
  const httpOnly = args.includes('--http-only');
  const expectedHtml = fs.readFileSync(path.resolve(__dirname,'../index.html'),'utf8');
  const attempts = httpOnly ? 3 : 12;
  for (let attempt=1; attempt<=attempts; attempt++) {
    try {
      await verifyHttp({expectedHtml});
      console.log('PASS: HTTPS, published HTML, five security headers, and '+privatePaths.length+' blocked internal/product paths');
      break;
    } catch(error) {
      if(attempt===attempts) throw error;
      console.log('Waiting for Cloudflare deployment: attempt '+attempt+'/'+attempts+'; '+error.message.split('\n')[0]);
      await new Promise(resolve=>setTimeout(resolve,5000));
    }
  }
  if (httpOnly) return;
  // The daily HTTP check uses Node alone; browsers are needed only for layout tests.
  const {chromium} = require('playwright');
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
}

module.exports = {verifyHttp};
if (require.main===module) main().catch(error=>{console.error(error.message);process.exitCode=1;});
