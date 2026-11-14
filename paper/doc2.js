// doc2.js -- Document 2: the research completion and data analysis manual.
//
// Built after the paper, in the same run, so that it can list every red
// placeholder the paper contains. Parts I to III are in doc2a.js, IV to VII in
// doc2b.js.
const L = require('./lib');
const { P, note, D } = L;

function build(meta) {
  const out = [];
  const add = (...xs) => { for (const x of xs) out.push(...(Array.isArray(x) ? x : [x])); };
  const t = {
    out, add, sheets: [], figureTitles: L.state.figTitles,
    part: (num, title) => add(L.H1(`Part ${num}. ${title}`, { breakBefore: true })),
    sec: (code, title) => { L.state.anchors.add(code); add(L.H2(`${code}  ${title}`)); },
  };
  const reds = Object.values(L.state.reds);
  const tp = (text, size, o = {}) => new D.Paragraph({ alignment: D.AlignmentType.CENTER,
    spacing: { before: o.before || 0, after: o.after ?? 120 },
    children: [new D.TextRun({ text, font: L.SANS, size, bold: o.bold, color: o.color })] });
  add(
    tp('COMPANION TO THE WORKING RESEARCH PAPER', 20,
      { before: 900, bold: true, color: L.GREY, after: 300 }),
    tp('Research Completion and', 44, { bold: true, color: '12324F', after: 40 }),
    tp('Data Analysis Manual', 44, { bold: true, color: '12324F', after: 200 }),
    tp('How to finish the physical validation, analyse its data, and complete the paper',
      24, { color: '12324F', after: 500 }),
    tp('Project: a decoder-health monitor for neural interfaces', 22, { after: 60 }),
    tp('Gayathri Nair, Central Bucks High School South', 22, { after: 400 }),
    tp(`Version of ${meta.date}`, 22, { bold: true, after: 400 }),
  );
  add(note([
    '**How the two documents fit together.** The working research paper holds '
    + `${reds.length} red items, ${L.REG.figures.length} figures and ${L.REG.tables.length} `
    + 'tables. This manual refers to them by the same numbers. Every red item has a code '
    + '(for example R6.3), and Section VII.4 of this manual lists all of them with the place '
    + 'each comes from. Figures and tables of the manual itself are numbered M1, M2 and so '
    + 'on, so that they cannot be confused with those of the paper.',
    'Pink cells in this manual are record sheets and checklists to be filled in. Grey boxes '
    + 'headed "Illustration" show arithmetic on invented numbers and are not results.',
  ]));
  add(P('**Contents.** Part I Completion Roadmap · Part II Physical Validation '
    + 'Documentation · Part III Experimental Data Collection · Part IV Data '
    + 'Processing and Quantitative Analysis · Part V Graph and Figure Generation · '
    + 'Part VI Completing Each Section of the Paper · Part VII Final Assembly and '
    + 'Quality Control', { run: { font: L.SANS, size: 20 } }));
  require('./doc2a')(t, meta);
  require('./doc2b')(t, meta);

  // literal codes written in the manual's text must still name the right items
  const want = { 'R0.1': 'WORKING TITLE', 'R1.1': 'BENCH RESULTS', 'R1.2': 'VERDICT', 'R4.1': 'VERSIONS',
    'R4.2': 'PINK COLUMNS', 'R5.1': 'TEMPERATURE SENSOR', 'R5.2': 'MODULATION DEPTH',
    'R5.11': 'DATES', 'R7.1': 'PREDICTION', 'R7.2': 'BENCH COLUMN', 'R7.4': 'VERDICT',
    'R9.1': 'QUESTIONS', 'R10.1': 'OBSERVED SIZE', 'R10.2': 'DEPARTURE',
    'R10.3': 'SOURCES OF ERROR', 'R11.1': 'CONCLUSION', 'R12.1': 'AUTHOR LIST',
    'R12.2': 'SENDELBACH', 'R12.3': 'COMMIT', 'R13.1': 'ACKNOWLEDGMENTS', 'R13.2': 'AI TOOLS' };
  for (const [id, word] of Object.entries(want)) {
    const r = L.state.reds[id];
    if (!r || !r.text.includes(word)) {
      throw new Error(`the manual names ${id} as the item about "${word}", but the paper's `
        + `${id} is: ${r ? r.text : 'missing'}`);
    }
  }
  return { children: out, sheets: t.sheets };
}

module.exports = { build };
