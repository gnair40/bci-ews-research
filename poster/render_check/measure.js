// measure.js -- does every panel fit, and is any text below 24 pt (32 px)?
//   python3 poster/render_check/preview.py
//   node poster/render_check/measure.js poster/render_check/out draft3
// Needs Node with Playwright. Exits non-zero if a panel overflows or any text is too small.
const { chromium } = require('playwright');
(async () => {
  const dir = require('path').resolve(process.argv[2]);
  let bad = 0;
  const b = await chromium.launch();
  // which draft: "draft2" (default) or "draft3". Draft 1 is kept as a record of the
  // first design and is not checked: its small type is the reason it was replaced.
  const which = process.argv[3] || 'draft2';
  const sets = { draft2: [['Left',1152],['Main',2304],['Right',1152]],
                 draft3: [['D3-Left',1152],['D3-Centre',2304],['D3-Right',1152]],
                 draft1: [['D1-Left',1152],['D1-Centre',2304],['D1-Right',1152]] };
  for (const [n, w] of sets[which]) {
    const p = await b.newPage({ viewport: { width: w, height: 3456 }, deviceScaleFactor: 1 });
    await p.goto('file://' + dir + '/' + n + '.html');
    await p.waitForLoadState('networkidle');
    await p.evaluate(() => document.fonts.ready);
    const info = await p.evaluate(() => {
      const r = document.body.querySelector('div');
      const kids = [...r.children].map(c => ({h: Math.round(c.getBoundingClientRect().height), bottom: Math.round(c.getBoundingClientRect().bottom), t: (c.textContent||'').trim().slice(0,46)}));
      // smallest rendered text, HTML and SVG
      const small = [];
      const walker = document.createTreeWalker(r, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        if (!node.nodeValue.trim()) continue;
        const el = node.parentElement;
        let fs = parseFloat(getComputedStyle(el).fontSize);
        const svg = el.closest('svg');
        if (svg && svg.viewBox && svg.viewBox.baseVal.width) fs *= svg.getBoundingClientRect().width / svg.viewBox.baseVal.width;
        if (fs < 31.9) small.push(fs.toFixed(1) + 'px: ' + node.nodeValue.trim().slice(0, 40));
      }
      // horizontal overflow of any element past the panel
      const wide = [...r.querySelectorAll('*')].filter(e => e.getBoundingClientRect().right > r.getBoundingClientRect().right + 1).map(e => e.tagName + ':' + (e.textContent||'').trim().slice(0,30)).slice(0,6);
      return { scroll: r.scrollHeight, client: r.clientHeight, kids, small, wide };
    });
    console.log(n, 'content', info.scroll, 'of', info.client, 'overflow', info.scroll - info.client, '| text under 32px:', info.small.length, '| past right edge:', info.wide.length);
    for (const k of info.kids) console.log('   ', String(k.h).padStart(5), 'bottom', String(k.bottom).padStart(5), k.t);
    for (const s of info.small.slice(0, 12)) console.log('      SMALL', s);
    for (const s of info.wide) console.log('      WIDE', s);
    if (info.scroll > info.client || info.small.length || info.wide.length) bad++;
    await p.screenshot({ path: dir + '/' + n + '.png', fullPage: false });
    await p.close();
  }
  await b.close();
  console.log(bad ? 'FAIL' : 'PASS -- every panel fits and no text is under 24 pt');
  process.exit(bad ? 1 : 0);
})();
