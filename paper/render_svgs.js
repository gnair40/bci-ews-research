// render_svgs.js -- turn paper/figures/src/*.svg into paper/figures/*.png
//
//     node paper/render_svgs.js
//
// A Word file cannot be relied on to draw SVG the same way everywhere, so each
// drawing is rendered once here, at three times its drawn size, and the PNG is
// what goes into the documents.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const SRC = path.join(__dirname, 'figures', 'src');
const OUT = path.join(__dirname, 'figures');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 3 });
  const names = fs.readdirSync(SRC).filter((f) => f.endsWith('.svg')).sort();
  const sizes = {};
  for (const f of names) {
    const svg = fs.readFileSync(path.join(SRC, f), 'utf8');
    const m = svg.match(/viewBox="0 0 ([\d.]+) ([\d.]+)"/);
    const w = Math.round(parseFloat(m[1]));
    const h = Math.round(parseFloat(m[2]));
    await page.setViewportSize({ width: w, height: h });
    const sized = svg.replace(/<svg /, `<svg style="display:block;width:${w}px;height:${h}px" `);
    await page.setContent(
      `<html><body style="margin:0;background:#fff">${sized}</body></html>`);
    const name = f.replace(/\.svg$/, '');
    await page.screenshot({ path: path.join(OUT, name + '.png'),
                            clip: { x: 0, y: 0, width: w, height: h } });
    sizes[name] = [w, h];
  }
  fs.writeFileSync(path.join(OUT, 'sizes.json'), JSON.stringify(sizes, null, 1) + '\n');
  await browser.close();
  console.log(`rendered ${names.length} drawings to paper/figures/`);
})();
