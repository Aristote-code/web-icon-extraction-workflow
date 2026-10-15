// Run inside an initialized Codex cua_repl session, not Node or the browser console.
// Bind `tab` through the documented cua API and read its pageAssets documentation first.
// `captureRoot` is an absolute path chosen for this run; import fs only for artifact I/O.
// This helper captures the current state. It does not click, submit, or crawl automatically.
async function createIconCapture(tab, captureRoot) {
  const fs = await import('node:fs/promises');
  const path = await import('node:path');
  const crypto = await import('node:crypto');
  const assets = await tab.capabilities.get('pageAssets');
  await fs.mkdir(path.join(captureRoot, 'captures'), {recursive:true});
  await fs.mkdir(path.join(captureRoot, 'originals'), {recursive:true});
  const existing = (await fs.readdir(path.join(captureRoot, 'captures')))
    .filter(name => /^\d+\.json(?:\.gz)?$/.test(name));
  let next = existing.length ? Math.max(...existing.map(name=>Number(name.split('.')[0])))+1 : 0;
  return async function capture(label) {
    const inventory = await assets.list();
    const dom = await tab.playwright.evaluate(() => ({
      url:location.href, title:document.title,
      svgs:[...document.querySelectorAll('svg')].map(e=>e.outerHTML),
      symbols:[...document.querySelectorAll('symbol')].map(e=>e.outerHTML),
      uses:[...document.querySelectorAll('use')].map(e=>e.getAttribute('href')||e.getAttribute('xlink:href')),
      links:[...document.querySelectorAll('a[href]')].map(e=>({
        text:e.innerText||e.getAttribute('aria-label')||'',href:e.href
      }))
    }));
    const bundle = await assets.bundle({inventoryId:inventory.id,kinds:['image','stylesheet']});
    const originals=[];
    for (const asset of bundle.assets) {
      if (asset.kind!=='image'||!asset.url.startsWith('http')) continue;
      const bytes=await fs.readFile(asset.path);
      const hash=crypto.createHash('sha256').update(bytes).digest('hex');
      const name=(asset.name||'image').split('#')[0].replace(/[^a-zA-Z0-9._-]/g,'-').slice(0,120);
      const relative='originals/'+hash.slice(0,10)+'-'+name;
      await fs.writeFile(path.join(captureRoot,relative),bytes);
      originals.push({kind:asset.kind,url:asset.url,name:asset.name,contentType:asset.contentType,path:relative});
    }
    const id=next++;
    await fs.writeFile(path.join(captureRoot,'captures',id+'.json'),JSON.stringify({
      label,dom,bundle:{assets:originals,failures:bundle.failures}
    }));
    return {capture:id,url:dom.url,inlineSvgs:dom.svgs.length,symbols:dom.symbols.length,
      downloadedOriginals:originals.length,failedDownloads:bundle.failures.length};
  };
}
