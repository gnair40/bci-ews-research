// measure.js -- does every panel fit, and is any text below the floor?
//   Drafts 2 and 3: 24 pt (32 px). Draft 4: 20 pt (27 px), and it reports how many
//   pieces of text sit between 20 and 24 pt so that they can be looked at.
//   python3 poster/render_check/preview.py
//   node poster/render_check/measure.js poster/render_check/out draft4
// Needs Node with Playwright. Exits non-zero if a panel overflows or any text is too small.
const { chromium } = require('playwright');
(async () => {
  const dir = require('path').resolve(process.argv[2]);
  let bad = 0;
  const b = await chromium.launch();
  // which draft: "draft2" (default), "draft3" or "draft4". Draft 1 is kept as a record of the
  // first design and is not checked: its small type is the reason it was replaced.
  const which = process.argv[3] || 'draft2';
  const sets = { draft2: [['Left',1152],['Main',2304],['Right',1152]],
                 draft3: [['D3-Left',1152],['D3-Centre',2304],['D3-Right',1152]],
                 draft4: [['D4-Left',1152],['D4-Centre',2304],['D4-Right',1152]],
                 draft1: [['D1-Left',1152],['D1-Centre',2304],['D1-Right',1152]] };
  // Draft 4 is 48 in tall, and allows captions, axis labels and table cells at 20 pt (27 px).
  // Every other draft is 36 in tall with a single floor of 24 pt (32 px).
  const H = which === 'draft4' ? 4608 : 3456;
  const FLOOR = which === 'draft4' ? 26.9 : 31.9;
  for (const [n, w] of sets[which]) {
    const p = await b.newPage({ viewport: { width: w, height: H }, deviceScaleFactor: 1 });
    await p.goto('file://' + dir + '/' + n + '.html');
    await p.waitForLoadState('networkidle');
    await p.evaluate(() => document.fonts.ready);
    const info = await p.evaluate((FLOOR) => {
      const r = document.body.querySelector('div');
      const kids = [...r.children].map(c => ({h: Math.round(c.getBoundingClientRect().height), bottom: Math.round(c.getBoundingClientRect().bottom), t: (c.textContent||'').trim().slice(0,46)}));
      // smallest rendered text, HTML and SVG
      const small = []; let mid = 0;
      const walker = document.createTreeWalker(r, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        if (!node.nodeValue.trim()) continue;
        const el = node.parentElement;
        let fs = parseFloat(getComputedStyle(el).fontSize);
        const svg = el.closest('svg');
        if (svg && svg.viewBox && svg.viewBox.baseVal.width) fs *= svg.getBoundingClientRect().width / svg.viewBox.baseVal.width;
        if (fs < FLOOR) small.push(fs.toFixed(1) + 'px: ' + node.nodeValue.trim().slice(0, 40));
        else if (fs < 31.9) mid++;
      }
      // horizontal overflow of any element past the panel
      const wide = [...r.querySelectorAll('*')].filter(e => e.getBoundingClientRect().right > r.getBoundingClientRect().right + 1).map(e => e.tagName + ':' + (e.textContent||'').trim().slice(0,30)).slice(0,6);
      return { scroll: r.scrollHeight, client: r.clientHeight, kids, small, wide, mid };
    }, FLOOR);
    console.log(n, 'content', info.scroll, 'of', info.client, 'overflow', info.scroll - info.client, '| text under the floor:', info.small.length, '| at caption size (20 to 24 pt):', info.mid, '| past right edge:', info.wide.length);
    for (const k of info.kids) console.log('   ', String(k.h).padStart(5), 'bottom', String(k.bottom).padStart(5), k.t);
    for (const s of info.small.slice(0, 12)) console.log('      SMALL', s);
    for (const s of info.wide) console.log('      WIDE', s);
    if (info.scroll > info.client || info.small.length || info.wide.length) bad++;
    await p.screenshot({ path: dir + '/' + n + '.png', fullPage: false });
    await p.close();
  }
  await b.close();
  console.log(bad ? 'FAIL' : 'PASS -- every panel fits and no text is under ' + (which === 'draft4' ? '20 pt' : '24 pt'));
  process.exit(bad ? 1 : 0);
})();
