// build.js -- write the two Word documents.
//
//     python3 paper/make_figures.py && node paper/render_svgs.js && node paper/build.js
//
// One program builds both, because they are two halves of one thing: the paper
// holds numbered red placeholders, and the manual must explain every one of them.
// The build stops with an error if
//   - a placeholder names a section of the manual that does not exist,
//   - the paper uses its figures or tables in a different order from registry.json,
//   - a table number written inside a red instruction no longer matches.
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const L = require('./lib');

const sh = (c) => execSync(c, { cwd: L.REPO }).toString().trim();
const v = JSON.parse(sh('python3 -c "import sys,json,numpy,pandas,scipy,matplotlib,h5py;'
  + 'print(json.dumps(dict(python=sys.version.split()[0],numpy=numpy.__version__,'
  + 'pandas=pandas.__version__,scipy=scipy.__version__,matplotlib=matplotlib.__version__,'
  + 'h5py=h5py.__version__)))"'));
const meta = {
  date: process.env.PAPER_DATE || '14 November 2026',
  repo: 'github.com/gnair40/bci-ews-research',
  branch: sh('git rev-parse --abbrev-ref HEAD'),
  // the documents are built from, and describe, the commit that came before them
  commit: process.env.PAPER_COMMIT || sh('git rev-parse --short HEAD'),
  versions: v,
};

// table numbers that are written out inside red instructions in doc1.js
const fixed = { b_gates: 13, b_sessions: 14, b_fa: 15, b_lead_type: 16, b_lead_sev: 17,
  b_undesigned: 18, b_corr: 19, b_rate: 20, b_app: 21, predictions: 22, compare: 23,
  errors: 24, deviations: 25 };
for (const [k, want] of Object.entries(fixed)) {
  if (L.tabNo(k) !== want) throw new Error(`Table ${k} is now ${L.tabNo(k)}; doc1.js says ${want}`);
}

const paper = require('./doc1').build(meta);
const same = (a, b) => a.length === b.length && a.every((x, i) => x === b[i]);
if (!same(L.state.figUsed, L.REG.figures)) {
  throw new Error('figure order differs from registry.json:\n' + L.state.figUsed.join(' '));
}
if (!same(L.state.tabUsed, L.REG.tables)) {
  throw new Error('table order differs from registry.json:\n' + L.state.tabUsed.join(' '));
}
const manual = require('./doc2').build(meta);
const missing = Object.values(L.state.reds).filter((r) => !L.state.anchors.has(r.see));
if (missing.length) {
  throw new Error('placeholders that point to no section of the manual:\n'
    + missing.map((r) => `${r.id} -> ${r.see}`).join('\n'));
}

const write = async (name, title, running, children) => {
  const doc = L.makeDoc({ title, running, children });
  const buf = await L.D.Packer.toBuffer(doc);
  fs.writeFileSync(path.join(L.HERE, name), buf);
  console.log(`wrote paper/${name}  (${Math.round(buf.length / 1024)} kB)`);
};
(async () => {
  await write('Working_Research_Paper.docx',
    'Seeing Failure Before It Shows: working research paper',
    `Seeing Failure Before It Shows  |  working research paper  |  draft of ${meta.date}`,
    paper);
  await write('Completion_Manual.docx',
    'Research Completion and Data Analysis Manual',
    `Research Completion and Data Analysis Manual  |  companion to the working paper  |  `
    + meta.date, manual);
  const reds = Object.values(L.state.reds);
  fs.writeFileSync(path.join(L.HERE, 'placeholders.json'), JSON.stringify(reds, null, 1) + '\n');
  console.log(`${reds.length} red placeholders in the paper, every one explained in the manual`);
  console.log(`${L.REG.figures.length} figures and ${L.REG.tables.length} tables in the paper`);
})();
