// extract.js -- read one rendered panel and list everything on it as simple drawing items.
//
//   node poster/pptx/extract.js <dir of rendered .html> <panel name> <width px> <height px> <out.json> <image dir>
//
// The panel is opened in a real browser, so every position below is where the browser
// actually put the thing. Nothing is redrawn from the builder's code. The Python writer
// (build_pptx.py) turns the list into PowerPoint text boxes and shapes.
//
// Kinds of item:
//   flow   a paragraph block: runs of text that PowerPoint may re-wrap inside its box
//   frag   one line (or part of a line) of text at an exact place; never re-wrapped
//   rect / round / ellipse / line / poly   shapes, from HTML boxes and from chart elements
//   img    a picture (the wiring drawings); rendered to PNG here
// Items that came from one chart or drawing share a group number, so the writer can
// group them and the whole chart moves as one object.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const EXTRACT = () => {
  const items = [], images = [], groups = {};
  let gid = 0;
  const root = document.body.querySelector('div');
  const px = v => parseFloat(v) || 0;
  const col = c => {
    const m = /rgba?\(([^)]+)\)/.exec(c || '');
    if (!m) return null;
    const p = m[1].split(/[,\s/]+/).filter(Boolean).map(parseFloat);
    const a = p.length > 3 ? p[3] : 1;
    if (!(a > 0)) return null;
    return { hex: p.slice(0, 3).map(v => Math.round(v).toString(16).padStart(2, '0')).join('').toUpperCase(), a };
  };
  const fam = f => f.split(',')[0].trim().replace(/^['"]|['"]$/g, '');
  const tstyle = el => {
    const cs = getComputedStyle(el);
    return { f: fam(cs.fontFamily), s: px(cs.fontSize), wt: parseInt(cs.fontWeight) || 400,
             it: cs.fontStyle === 'italic', c: (col(cs.color) || { hex: '000000' }).hex,
             ls: cs.letterSpacing === 'normal' ? 0 : px(cs.letterSpacing),
             up: cs.textTransform === 'uppercase',
             lh: cs.lineHeight === 'normal' ? 0 : px(cs.lineHeight), pre: cs.whiteSpace.startsWith('pre') };
  };
  const isSvg = el => el.namespaceURI === 'http://www.w3.org/2000/svg';
  // Source Serif 4 changes shape with size in the browser (large type is drawn narrower).
  // PowerPoint does not do that: it draws every size with the font's standard shape, which
  // is wider at heading sizes. `fit` is how much to shrink the type so its width is the same.
  // The standard shape is the font's optical size 14: measured here, the installed static
  // files are exactly as wide as the browser's font forced to that setting.
  const probe = document.createElement('span');
  probe.style.cssText = 'position:absolute;left:-99999px;top:0;visibility:hidden;white-space:nowrap';
  document.body.appendChild(probe);
  const fitCache = {};
  const fit = (el, text) => {
    const cs = getComputedStyle(el);
    if (!/Source Serif/.test(cs.fontFamily)) return 1;
    const key = cs.fontSize + '|' + cs.fontWeight;
    if (!(key in fitCache)) {
      probe.style.font = cs.font;
      probe.style.letterSpacing = cs.letterSpacing;
      probe.textContent = 'Seeing failure before it shows 0123456789';
      probe.style.fontOpticalSizing = 'auto';
      const a = probe.getBoundingClientRect().width;
      probe.style.fontVariationSettings = '"opsz" 14';
      const n = probe.getBoundingClientRect().width;
      probe.style.fontVariationSettings = 'normal';
      fitCache[key] = n > 0 ? Math.min(1, a / n) : 1;
    }
    return fitCache[key];
  };

  // ---- HTML boxes: background, borders, rounded corners ---------------------------
  function box(el, cs) {
    const r = el.getBoundingClientRect();
    if (r.width < 0.5 && r.height < 0.5) return;
    const bg = col(cs.backgroundColor);
    const sides = ['Top', 'Right', 'Bottom', 'Left'].map(s => {
      const b = { w: px(cs['border' + s + 'Width']), st: cs['border' + s + 'Style'], c: col(cs['border' + s + 'Color']) };
      return (b.w > 0 && b.st !== 'none' && b.st !== 'hidden' && b.c) ? b : null;
    });
    if (!bg && !sides.some(Boolean)) return;
    let rad = px(cs.borderTopLeftRadius);
    if (cs.borderTopLeftRadius.includes('%')) rad = Math.min(r.width, r.height) * parseFloat(cs.borderTopLeftRadius) / 100;
    const round = rad * 2 >= Math.min(r.width, r.height) - 0.5;
    const kind = (round && Math.abs(r.width - r.height) < 2) ? 'ellipse' : (rad > 0.5 ? 'round' : 'rect');
    const uni = sides.every(Boolean) && sides.every(b => b.w === sides[0].w && b.st === sides[0].st && b.c.hex === sides[0].c.hex);
    if (uni) {
      const bw = sides[0].w;      // a CSS border sits inside the box; a PowerPoint outline straddles the edge
      items.push({ k: kind, x: r.left + bw / 2, y: r.top + bw / 2, w: r.width - bw, h: r.height - bw,
                   rad: Math.max(0, rad - bw / 2), fill: bg, line: { c: sides[0].c, w: bw, dash: sides[0].st } });
      return;
    }
    if (bg) items.push({ k: kind, x: r.left, y: r.top, w: r.width, h: r.height, rad, fill: bg, line: null });
    sides.forEach((b, i) => {
      if (!b) return;
      const h = b.w / 2;
      const s = [[r.left, r.top + h, r.right, r.top + h], [r.right - h, r.top, r.right - h, r.bottom],
                 [r.left, r.bottom - h, r.right, r.bottom - h], [r.left + h, r.top, r.left + h, r.bottom]][i];
      items.push({ k: 'line', x1: s[0], y1: s[1], x2: s[2], y2: s[3], line: { c: b.c, w: b.w, dash: b.st } });
    });
  }

  // ---- text ----------------------------------------------------------------------
  // A block is "simple" when it holds only text and plain inline tags. Then it becomes
  // one text box that PowerPoint can re-wrap. Anything else is placed line by line.
  function scanInline(el, acc) {
    for (const n of el.childNodes) {
      if (n.nodeType === 3) { if (n.nodeValue.trim()) acc.text = true; continue; }
      if (n.nodeType !== 1 || n.tagName === 'BR') continue;
      const d = getComputedStyle(n).display;
      if (d === 'none') continue;
      if (d !== 'inline' || isSvg(n) || n.tagName === 'IMG') { acc.ok = false; return; }
      scanInline(n, acc);
      if (!acc.ok) return;
    }
  }
  function flow(el, cs) {
    const r = el.getBoundingClientRect();
    const bl = px(cs.borderLeftWidth), br = px(cs.borderRightWidth), bt = px(cs.borderTopWidth), bb = px(cs.borderBottomWidth);
    const x = r.left + bl + px(cs.paddingLeft), y = r.top + bt + px(cs.paddingTop);
    const w = r.width - bl - br - px(cs.paddingLeft) - px(cs.paddingRight);
    const h = r.height - bt - bb - px(cs.paddingTop) - px(cs.paddingBottom);
    const paras = [[]];
    const walkT = (node, hl) => {
      for (const n of node.childNodes) {
        if (n.nodeType === 3) {
          const st = tstyle(n.parentElement);
          let t = n.nodeValue;
          if (!st.pre) t = t.replace(/\s+/g, ' ');
          if (st.up) t = t.toUpperCase();
          if (t) paras[paras.length - 1].push(Object.assign({ t, fit: fit(n.parentElement, t), hl }, st));
        } else if (n.nodeType === 1) {
          if (n.tagName === 'BR') { paras.push([]); continue; }
          const c2 = getComputedStyle(n);
          if (c2.display === 'none') continue;
          const bg = col(c2.backgroundColor);          // a highlighter stroke: it must travel with its words
          walkT(n, bg ? bg.hex : hl);
        }
      }
    };
    walkT(el, null);
    for (const runs of paras) {                          // collapse spaces the way the browser did
      let prevSpace = true;
      for (const run of runs) {
        if (run.pre) { prevSpace = false; continue; }
        if (prevSpace) run.t = run.t.replace(/^ +/, '');
        if (run.t) prevSpace = run.t.endsWith(' ');
      }
      for (let i = runs.length - 1; i >= 0; i--) {
        if (runs[i].pre) break;
        runs[i].t = runs[i].t.replace(/ +$/, '');
        if (runs[i].t) break;
      }
      for (let i = runs.length - 1; i >= 0; i--) if (!runs[i].t) runs.splice(i, 1);
    }
    while (paras.length > 1 && !paras[paras.length - 1].length) paras.pop();
    if (!paras.some(p => p.length)) return;
    const range = document.createRange();
    range.selectNodeContents(el);
    const tops = new Set();
    for (const q of range.getClientRects()) if (q.width > 0.5) tops.add(Math.round(q.top / 4));
    const al = { center: 'center', right: 'right', end: 'right' }[cs.textAlign] || 'left';
    items.push({ k: 'flow', x, y, w, h, al, paras, lines: Math.max(1, tops.size), lh: cs.lineHeight === 'normal' ? 0 : px(cs.lineHeight) });
  }
  function frags(tn) {
    const st = tstyle(tn.parentElement), txt = tn.nodeValue, re = /\S+/g, lines = [];
    const range = document.createRange();
    let m;
    while ((m = re.exec(txt))) {
      range.setStart(tn, m.index);
      range.setEnd(tn, m.index + m[0].length);
      const rs = range.getClientRects();
      if (!rs.length) continue;
      const a = rs[0], z = rs[rs.length - 1], last = lines[lines.length - 1];
      if (last && Math.abs(last.top - a.top) < 3 && a.left >= last.right - 2) {
        last.right = Math.max(last.right, z.right); last.bottom = Math.max(last.bottom, a.bottom); last.end = m.index + m[0].length;
      } else lines.push({ top: a.top, bottom: a.bottom, left: a.left, right: z.right, start: m.index, end: m.index + m[0].length });
    }
    for (const ln of lines) {
      let t = txt.slice(ln.start, ln.end);
      if (!st.pre) t = t.replace(/\s+/g, ' ');
      if (st.up) t = t.toUpperCase();
      items.push(Object.assign({ k: 'frag', x: ln.left, y: ln.top, w: ln.right - ln.left, h: ln.bottom - ln.top, t, al: 'left', rot: 0,
                                 fit: fit(tn.parentElement, t) }, st));
    }
  }
  function bullet(el, cs) {
    const r = el.getBoundingClientRect(), fs = px(cs.fontSize), lh = px(cs.lineHeight) || fs * 1.3, d = fs * 0.3;
    items.push({ k: 'ellipse', x: r.left - fs * 0.66 - d / 2, y: r.top + lh / 2 - d / 2 + fs * 0.03, w: d, h: d, rad: 0,
                 fill: col(cs.color), line: null });
  }

  // ---- charts and drawings (inline SVG) ----------------------------------------------
  function dashOf(arr, sw) {
    if (!arr || arr === 'none') return null;
    const first = parseFloat(arr);
    if (!(first > 0)) return null;
    return first <= sw * 1.6 ? 'sysDot' : (first <= sw * 3.2 ? 'sysDash' : 'dash');
  }
  function pattern(el, ref) {
    const id = /#([^"')]+)/.exec(ref);
    const p = id && el.ownerSVGElement.querySelector('#' + CSS.escape(id[1]));
    if (!p) return null;
    const bgEl = p.querySelector('rect'), fgEl = p.querySelector('line, path');
    return { bg: (col(bgEl && getComputedStyle(bgEl).fill) || { hex: 'FFFFFF' }).hex,
             fg: (col(fgEl && getComputedStyle(fgEl).stroke) || { hex: '999999' }).hex };
  }
  function pathPoints(el, P) {
    const d = el.getAttribute('d') || '';
    const toks = d.match(/[a-zA-Z]|-?\d*\.?\d+(?:e[-+]?\d+)?/g) || [];
    if (/[AaSsTt]/.test(d.replace(/e[-+]?\d+/g, ''))) {           // arcs: follow the drawn outline instead
      const n = 72, len = el.getTotalLength(), pts = [];
      for (let i = 0; i <= n; i++) { const q = el.getPointAtLength(len * i / n); pts.push(P(q.x, q.y)); }
      return [{ pts, closed: /[zZ]/.test(d) }];
    }
    const subs = []; let cur = null, i = 0, cmd = '', x = 0, y = 0, sx = 0, sy = 0;
    const num = () => parseFloat(toks[i++]);
    const curve = (p0, p1, p2, p3) => { for (let k = 1; k <= 12; k++) { const t = k / 12, u = 1 - t;
      cur.pts.push(P(u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                     u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1])); } };
    while (i < toks.length) {
      if (/[a-zA-Z]/.test(toks[i])) cmd = toks[i++];
      const rel = cmd === cmd.toLowerCase(), C = cmd.toUpperCase();
      if (C === 'Z') { if (cur) cur.closed = true; x = sx; y = sy; continue; }
      if (C === 'M') { const nx = num(), ny = num(); x = rel ? x + nx : nx; y = rel ? y + ny : ny; sx = x; sy = y;
        cur = { pts: [P(x, y)], closed: false }; subs.push(cur); cmd = rel ? 'l' : 'L'; continue; }
      if (!cur) { cur = { pts: [P(x, y)], closed: false }; subs.push(cur); }
      if (C === 'L') { const nx = num(), ny = num(); x = rel ? x + nx : nx; y = rel ? y + ny : ny; cur.pts.push(P(x, y)); }
      else if (C === 'H') { const nx = num(); x = rel ? x + nx : nx; cur.pts.push(P(x, y)); }
      else if (C === 'V') { const ny = num(); y = rel ? y + ny : ny; cur.pts.push(P(x, y)); }
      else if (C === 'C') { const a = [num(), num(), num(), num(), num(), num()].map((v, j) => rel ? v + (j % 2 ? y : x) : v);
        curve([x, y], [a[0], a[1]], [a[2], a[3]], [a[4], a[5]]); x = a[4]; y = a[5]; }
      else if (C === 'Q') { const a = [num(), num(), num(), num()].map((v, j) => rel ? v + (j % 2 ? y : x) : v);
        const c1 = [x + 2 / 3 * (a[0] - x), y + 2 / 3 * (a[1] - y)], c2 = [a[2] + 2 / 3 * (a[0] - a[2]), a[3] + 2 / 3 * (a[1] - a[3])];
        curve([x, y], c1, c2, [a[2], a[3]]); x = a[2]; y = a[3]; }
      else i++;
    }
    return subs;
  }
  function svgEl(el, g) {
    const tag = el.tagName.toLowerCase();
    if (['defs', 'marker', 'pattern', 'title', 'desc', 'clippath', 'style'].includes(tag)) return;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    if (tag === 'g' || tag === 'svg' || tag === 'a') { for (const c of el.children) svgEl(c, g); return; }
    const m = el.getScreenCTM();
    if (!m) return;
    const P = (x, y) => [m.a * x + m.c * y + m.e, m.b * x + m.d * y + m.f];
    const sc = Math.sqrt(Math.abs(m.a * m.d - m.b * m.c));
    const op = parseFloat(cs.opacity);
    if (tag === 'text') {
      const t = el.textContent.replace(/\s+/g, ' ').trim();
      if (!t) return;
      const r = el.getBoundingClientRect();
      const rot = /rotate\(\s*(-?[\d.]+)/.exec(el.getAttribute('transform') || '');
      const ang = rot ? parseFloat(rot[1]) : 0;
      let x = r.left, y = r.top, w = r.width, h = r.height;
      if (Math.abs(Math.abs(ang) - 90) < 1) { const cx = x + w / 2, cy = y + h / 2; w = r.height; h = r.width; x = cx - w / 2; y = cy - h / 2; }
      const anchor = cs.textAnchor || 'start';
      items.push({ k: 'frag', g, x, y, w, h, t, al: anchor === 'middle' ? 'center' : (anchor === 'end' ? 'right' : 'left'),
                   rot: ang ? ((ang % 360) + 360) % 360 : 0, f: fam(cs.fontFamily), s: px(cs.fontSize) * sc,
                   wt: parseInt(cs.fontWeight) || 400, it: false, c: (col(cs.fill) || { hex: '000000' }).hex,
                   ls: cs.letterSpacing === 'normal' ? 0 : px(cs.letterSpacing) * sc, up: false, lh: 0, pre: false });
      return;
    }
    let fill = null, patt = null;
    if (cs.fill && cs.fill.startsWith('url(')) patt = pattern(el, cs.fill);
    else if (cs.fill !== 'none') { fill = col(cs.fill); if (fill) fill.a *= (parseFloat(cs.fillOpacity) || 1) * op; }
    let line = null;
    if (cs.stroke && cs.stroke !== 'none') {
      const c = col(cs.stroke), w = px(cs.strokeWidth) * sc;
      if (c && w > 0) { c.a *= (parseFloat(cs.strokeOpacity) || 1) * op;
        line = { c, w, dash: dashOf(cs.strokeDasharray, px(cs.strokeWidth)), arrow: !!(cs.markerEnd && cs.markerEnd !== 'none') }; }
    }
    if (!fill && !patt && !line) return;
    const flat = Math.abs(m.b) < 1e-6 && Math.abs(m.c) < 1e-6;
    const v = n => el[n].baseVal.value;
    if (tag === 'line') { const a = P(v('x1'), v('y1')), b = P(v('x2'), v('y2'));
      if (line) items.push({ k: 'line', g, x1: a[0], y1: a[1], x2: b[0], y2: b[1], line }); return; }
    if (tag === 'rect' && flat) { const a = P(v('x'), v('y')); const rx = el.rx.baseVal.value * sc;
      items.push({ k: rx > 0.5 ? 'round' : 'rect', g, x: a[0], y: a[1], w: v('width') * m.a, h: v('height') * m.d, rad: rx, fill, patt, line }); return; }
    if (tag === 'circle' && flat) { const r = v('r'), a = P(v('cx') - r, v('cy') - r);
      items.push({ k: 'ellipse', g, x: a[0], y: a[1], w: 2 * r * m.a, h: 2 * r * m.d, rad: 0, fill, patt, line }); return; }
    if (tag === 'ellipse' && flat) { const a = P(v('cx') - v('rx'), v('cy') - v('ry'));
      items.push({ k: 'ellipse', g, x: a[0], y: a[1], w: 2 * v('rx') * m.a, h: 2 * v('ry') * m.d, rad: 0, fill, patt, line }); return; }
    let subs = [];
    if (tag === 'polyline' || tag === 'polygon') subs = [{ pts: [...el.points].map(q => P(q.x, q.y)), closed: tag === 'polygon' }];
    else if (tag === 'path') subs = pathPoints(el, P);
    else if (tag === 'rect') { const x = v('x'), y = v('y'), w = v('width'), h = v('height');
      subs = [{ pts: [P(x, y), P(x + w, y), P(x + w, y + h), P(x, y + h)], closed: true }]; }
    for (const s of subs) if (s.pts.length > 1) items.push({ k: 'poly', g, pts: s.pts, closed: s.closed, fill, patt, line });
  }
  function svgRoot(svg) {
    const r = svg.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return;
    const g = ++gid;
    groups[g] = (svg.getAttribute('aria-label') || '').slice(0, 90);
    for (const c of svg.children) svgEl(c, g);
  }

  // ---- the walk --------------------------------------------------------------------
  function walk(el) {
    const tag = el.tagName.toLowerCase();
    if (['script', 'style', 'link', 'meta', 'title', 'template'].includes(tag)) return;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    if (tag === 'svg') { svgRoot(el); return; }
    if (tag === 'img') {
      const r = el.getBoundingClientRect();
      images.push({ src: el.src, w: r.width, h: r.height });
      items.push({ k: 'img', id: images.length - 1, x: r.left, y: r.top, w: r.width, h: r.height, alt: el.getAttribute('alt') || '' });
      return;
    }
    if (el !== root) box(el, cs);
    if (cs.display === 'list-item') bullet(el, cs);
    if (['block', 'list-item', 'table-cell', 'flow-root'].includes(cs.display) && px(cs.textIndent) === 0) {
      const acc = { ok: true, text: false };
      scanInline(el, acc);
      if (acc.ok && acc.text) { flow(el, cs); return; }
    }
    for (const n of el.childNodes) {
      if (n.nodeType === 3) { if (n.nodeValue.trim()) frags(n); }
      else if (n.nodeType === 1) walk(n);
    }
  }
  walk(root);
  probe.remove();
  return { items, images, groups, fits: fitCache, text: root.textContent };
};

(async () => {
  const [dir, name, W, H, out, imgDir] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: +W, height: +H }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.resolve(dir, name + '.html'));
  await p.waitForLoadState('networkidle');
  await p.evaluate(() => document.fonts.ready);
  const data = await p.evaluate(EXTRACT);
  await p.close();
  fs.mkdirSync(imgDir, { recursive: true });
  for (let i = 0; i < data.images.length; i++) {           // each picture on its own, at twice its printed size
    const im = data.images[i], w = Math.ceil(im.w), h = Math.ceil(im.h);
    const tmp = path.resolve(imgDir, `_${name}_${i}.html`);
    fs.writeFileSync(tmp, `<!doctype html><html><body style="margin:0;background:transparent"><img src="${im.src}" style="display:block;width:${w}px;height:${h}px"></body></html>`);
    const q = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
    await q.goto('file://' + tmp);
    await q.waitForLoadState('networkidle');
    im.png = path.resolve(imgDir, `${name}_${i}.png`);
    await q.screenshot({ path: im.png, omitBackground: true });
    await q.close();
    fs.unlinkSync(tmp);
  }
  await b.close();
  fs.writeFileSync(out, JSON.stringify(data));
  const n = {};
  for (const it of data.items) n[it.k] = (n[it.k] || 0) + 1;
  console.log(name, JSON.stringify(n), 'groups', Object.keys(data.groups).length);
})();
