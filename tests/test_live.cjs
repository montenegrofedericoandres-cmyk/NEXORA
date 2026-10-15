const assert = require('node:assert/strict');
const {test} = require('node:test');
const {verifyHttp} = require('../scripts/verify_live.cjs');

const html = '<!doctype html><title>NEXORA fixture</title>';
const headers = {
  'content-security-policy': "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
  'x-content-type-options': 'nosniff',
  'x-frame-options': 'DENY',
  'referrer-policy': 'no-referrer',
  'permissions-policy': 'camera=(), microphone=(), geolocation=()'
};

function fixture({homeStatus=200,homeHtml=html,homeHeaders=headers,privateStatus=404}={}) {
  const calls = [];
  const cancelled = [];
  return {
    calls, cancelled,
    fetchImpl: async (href,options) => {
      const pathname = new URL(href).pathname;
      calls.push({href,options,pathname});
      if (pathname==='/') return new Response(homeHtml,{status:homeStatus,headers:homeHeaders});
      return {
        status:privateStatus,
        body:{cancel:async()=>{cancelled.push(pathname);}},
        text:async()=>{throw new Error('Private response body must never be read');}
      };
    }
  };
}

test('HTTPS, exact content, five headers and ten private paths pass without a browser dependency',async()=>{
  const fake = fixture();
  await verifyHttp({expectedHtml:html,fetchImpl:fake.fetchImpl});
  assert.equal(fake.calls.length,11);
  assert.equal(new Set(fake.calls.map(call=>call.pathname)).size,11);
  assert.equal(fake.cancelled.length,10);
  assert.ok(fake.calls.some(call=>call.pathname==='/.git/HEAD'));
  assert.ok(fake.calls.some(call=>call.pathname==='/producto.xlsx'));
  for (const {href,options} of fake.calls) {
    assert.equal(new URL(href).protocol,'https:');
    assert.equal(options.redirect,'manual');
    assert.ok(options.signal instanceof AbortSignal);
    assert.equal(options.signal,fake.calls[0].options.signal);
  }
});

test('a mismatched page fails without putting either page body in the error',async()=>{
  const fake = fixture({homeHtml:'PRIVATE_RESPONSE_SENTINEL'});
  await assert.rejects(verifyHttp({expectedHtml:html,fetchImpl:fake.fetchImpl}),error=>{
    assert.match(error.message,/Published page must match main/);
    assert.ok(!error.message.includes('PRIVATE_RESPONSE_SENTINEL'));
    assert.ok(!error.message.includes(html));
    return true;
  });
  assert.equal(fake.calls.length,1);
});

test('every missing security header fails',async t=>{
  for (const name of Object.keys(headers)) await t.test(name,async()=>{
    const changed = {...headers};
    delete changed[name];
    const fake = fixture({homeHeaders:changed});
    await assert.rejects(verifyHttp({expectedHtml:html,fetchImpl:fake.fetchImpl}),/Security header mismatch/);
  });
});

test('a weakened content security policy fails',async()=>{
  const fake = fixture({homeHeaders:{...headers,'content-security-policy':"default-src *; form-action *"}});
  await assert.rejects(verifyHttp({expectedHtml:html,fetchImpl:fake.fetchImpl}),/Security header mismatch/);
});

test('a private path returning content or a redirect fails and its body is cancelled',async t=>{
  for (const status of [200,301,403,500]) await t.test(String(status),async()=>{
    const fake = fixture({privateStatus:status});
    await assert.rejects(verifyHttp({expectedHtml:html,fetchImpl:fake.fetchImpl}),/Internal\/product path must return 404/);
    assert.deepEqual(fake.cancelled,['/.git/HEAD']);
  });
});

test('homepage redirects and errors fail',async t=>{
  for (const status of [301,404,503]) await t.test(String(status),async()=>{
    const fake = fixture({homeStatus:status});
    await assert.rejects(verifyHttp({expectedHtml:html,fetchImpl:fake.fetchImpl}),/Public homepage must return 200/);
    assert.equal(fake.calls.length,1);
  });
});

test('HTTP is rejected before making a request',async()=>{
  const fake = fixture();
  await assert.rejects(verifyHttp({expectedHtml:html,baseUrl:new URL('http://example.test/'),fetchImpl:fake.fetchImpl}),/must use HTTPS/);
  assert.equal(fake.calls.length,0);
});
