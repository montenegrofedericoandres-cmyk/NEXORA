// Browser checks for the static site. Run after scripts/build_site.py.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const {chromium} = require('playwright');
const root = path.resolve(__dirname, '..', 'dist');

(async () => {
  const server = http.createServer((request, response) => {
    const isHome = request.url === '/' || request.url === '/index.html';
    response.writeHead(isHome ? 200 : 404, {'Content-Type':'text/html; charset=utf-8'});
    response.end(fs.readFileSync(path.join(root, isHome ? 'index.html' : '404.html')));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const url = 'http://127.0.0.1:' + server.address().port + '/';
  let browser;
  try {
    browser = await chromium.launch({headless:true});
    for (const width of [320, 360, 390, 412, 768, 1280]) {
      const page = await browser.newPage({viewport:{width,height:900},isMobile:width<768,hasTouch:width<768});
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      const response = await page.goto(url);
      const result = await page.evaluate(() => ({
        width: innerWidth,
        documentWidth: document.documentElement.scrollWidth,
        overflow: [...document.querySelectorAll('body *')].filter(element => {
          const rect = element.getBoundingClientRect();
          return rect.width && (rect.right > innerWidth+1 || rect.left < -1);
        }).map(element => element.tagName),
        heading: document.querySelector('h1')?.textContent,
        prelaunch: document.body.textContent.includes('Próximamente disponible.'),
        links: [...document.querySelectorAll('a')].map(element => element.getAttribute('href')),
        contactHeight: document.querySelector('.contact').getBoundingClientRect().height,
        scripts: document.scripts.length,
        forms: document.forms.length,
        downloads: document.querySelectorAll('[download]').length
      }));
      console.log(JSON.stringify({requestedWidth:width,...result,errors}));
      assert.equal(response.status(),200);
      assert.equal(result.width,width,'Viewport metadata must match mobile width');
      assert.equal(result.documentWidth,width,'No horizontal page overflow');
      assert.deepEqual(result.overflow,[],'All content must fit the viewport');
      assert.deepEqual(errors,[],'No browser JavaScript errors');
      assert.ok(result.heading && result.prelaunch,'Main heading and prelaunch notice visible');
      assert.ok(result.contactHeight >= 44,'Primary contact target must be large enough to tap');
      assert.ok(result.links.every(href=>href.startsWith('mailto:nexoraproductosdigitales@gmail.com')),'Only contact links enabled');
      assert.equal(result.scripts+result.forms+result.downloads,0,'Payments and digital delivery remain disabled');
      await page.getByRole('link',{name:'Consultar disponibilidad',exact:true}).focus();
      assert.ok(await page.locator('.contact').evaluate(element=>element===document.activeElement),'Contact accessible by keyboard');
      await page.close();
    }
    const missing = await browser.newPage();
    assert.equal((await missing.goto(url+'no-existe')).status(),404);
    assert.ok(await missing.getByRole('link',{name:'Volver al inicio de NEXORA'}).isVisible());
    await missing.close();
    console.log('PASS: six mobile/tablet/desktop viewports, contact accessibility, 404, and disabled checkout/delivery');
  } finally {
    await browser?.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
