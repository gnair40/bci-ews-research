// lib.js -- the Word building blocks that both documents are made from.
//
// Nothing here knows any science. It only knows how to lay out a heading, a
// paragraph, a table, a figure, a red placeholder and a space to be filled.
//
// Inline markup understood in every text string:
//   **bold**   ~italic~   `file or command`   and the token a red() call returns.
const fs = require('fs');
const path = require('path');
const D = require('docx');

const HERE = __dirname;
const REPO = path.dirname(HERE);
const REG = JSON.parse(fs.readFileSync(path.join(HERE, 'registry.json'), 'utf8'));

const RED = 'C00000';
const PINK = 'FBE9E9';
const GREY = '4D4D4D';
const RULE = '8C8C8C';
const HEAD_FILL = 'DCE6F0';
const NOTE_FILL = 'EEF3F8';
const CODE_FILL = 'F2F2F2';
const SERIF = 'Times New Roman';
const SANS = 'Arial';
const MONO = 'Courier New';
const W = 9360;                      // text width in twentieths of a point (6.5 in)
const BODY = 23;                     // 11.5 pt, in half-points
const SMALL = 19;                    // 9.5 pt, tables and captions

// ---------------------------------------------------------------------------
// state shared by one build: red placeholders, figure and table numbering
// ---------------------------------------------------------------------------
const state = {
  reds: {},            // id -> {id, section, text, from, see}
  redCount: {},
  section: 0,          // current section of the paper
  figUsed: [],
  figTitles: {},       // key -> title of each figure of the paper
  tabUsed: [],
  anchors: new Set(),  // section numbers that exist in the manual
  mFig: 0,
  mTab: 0,
  listInstance: 0,
};

/** Register a red placeholder of the paper and return the token that prints it.
 *  text: the instruction, printed in capitals.
 *  from: where the missing item comes from (a file and field, a sheet, a photograph).
 *  see:  the section of the manual that explains how to produce it. */
function red(text, from, see) {
  if (!from || !see) throw new Error(`placeholder without a source or a manual section: ${text}`);
  const s = state.section;
  state.redCount[s] = (state.redCount[s] || 0) + 1;
  const id = `R${s}.${state.redCount[s]}`;
  state.reds[id] = { id, section: s, text: text.toUpperCase(), plain: text, from, see };
  return `⟦${id}⟧`;
}

const figNo = (key) => {
  const i = REG.figures.indexOf(key);
  if (i < 0) throw new Error(`figure not in registry.json: ${key}`);
  return i + 1;
};
const tabNo = (key) => {
  const i = REG.tables.indexOf(key);
  if (i < 0) throw new Error(`table not in registry.json: ${key}`);
  return i + 1;
};
const F = (key) => `Figure ${figNo(key)}`;
const T = (key) => `Table ${tabNo(key)}`;

// ---------------------------------------------------------------------------
// inline text
// ---------------------------------------------------------------------------
function rich(text, base = {}) {
  const b = { font: SERIF, size: BODY, ...base };
  const runs = [];
  const re = /(\*\*[^*]+\*\*|~[^~]+~|`[^`]+`|⟦[^⟧]+⟧)/g;
  let last = 0;
  let m;
  const plain = (s) => { if (s) runs.push(new D.TextRun({ text: s, ...b })); };
  while ((m = re.exec(text))) {
    plain(text.slice(last, m.index));
    const t = m[0];
    if (t.startsWith('**')) runs.push(new D.TextRun({ text: t.slice(2, -2), ...b, bold: true }));
    else if (t.startsWith('~')) runs.push(new D.TextRun({ text: t.slice(1, -1), ...b, italics: true }));
    else if (t.startsWith('`')) {
      runs.push(new D.TextRun({ text: t.slice(1, -1), ...b, font: MONO, size: b.size - 2 }));
    } else {
      const r = state.reds[t.slice(1, -1)];
      if (!r) throw new Error(`unknown placeholder token ${t}`);
      runs.push(new D.TextRun({ text: `[${r.id}: ${r.text}]`, ...b, bold: true, color: RED }));
    }
    last = re.lastIndex;
  }
  plain(text.slice(last));
  return runs;
}

/** A run of plain red instruction text, for use inside spaces and boxes. */
const redRuns = (text, size = SMALL) => [new D.TextRun({ text, font: SANS, size, bold: true,
  color: RED })];

// ---------------------------------------------------------------------------
// paragraphs
// ---------------------------------------------------------------------------
function P(text, o = {}) {
  return new D.Paragraph({
    children: rich(text, o.run),
    spacing: { after: o.after ?? 150, line: o.line ?? 290 },
    alignment: o.align,
    indent: o.indent,
    keepNext: o.keepNext,
  });
}
const H1 = (text, o = {}) => new D.Paragraph({ heading: D.HeadingLevel.HEADING_1,
  children: [new D.TextRun({ text })], pageBreakBefore: o.breakBefore ?? false });
const H2 = (text) => new D.Paragraph({ heading: D.HeadingLevel.HEADING_2,
  children: [new D.TextRun({ text })] });
const H3 = (text) => new D.Paragraph({ heading: D.HeadingLevel.HEADING_3,
  children: [new D.TextRun({ text })] });

function bullets(items, o = {}) {
  return items.map((t) => new D.Paragraph({
    children: rich(t, o.run), numbering: { reference: 'bul', level: 0 },
    spacing: { after: 70, line: 280 },
  }));
}
function numbered(items, o = {}) {
  const instance = ++state.listInstance;
  return items.map((t) => new D.Paragraph({
    children: rich(t, o.run), numbering: { reference: 'num', level: 0, instance },
    spacing: { after: 70, line: 280 },
  }));
}
/** A shaded box for a status statement or a caution. */
function note(text, o = {}) {
  const lines = Array.isArray(text) ? text : [text];
  return lines.map((t, i) => new D.Paragraph({
    children: rich(t, { font: SANS, size: 20, ...o.run }),
    shading: { type: D.ShadingType.CLEAR, color: 'auto', fill: o.fill || NOTE_FILL },
    border: { left: { style: D.BorderStyle.SINGLE, size: 18, color: o.bar || '1B5A8E', space: 8 } },
    spacing: { before: i === 0 ? 80 : 0, after: i === lines.length - 1 ? 180 : 0, line: 276 },
    indent: { left: 160, right: 120 },
  }));
}
/** Commands or file contents, exactly as typed. */
function code(lines) {
  const ls = Array.isArray(lines) ? lines : lines.split('\n');
  return ls.map((t, i) => new D.Paragraph({
    children: [new D.TextRun({ text: t || ' ', font: MONO, size: 17 })],
    shading: { type: D.ShadingType.CLEAR, color: 'auto', fill: CODE_FILL },
    spacing: { before: i === 0 ? 60 : 0, after: i === ls.length - 1 ? 160 : 0, line: 250 },
    indent: { left: 200, right: 120 },
  }));
}
/** A formula on its own line, with its meaning underneath when given. */
function formula(text, where) {
  const out = [new D.Paragraph({
    children: [new D.TextRun({ text, font: 'Cambria Math', size: BODY + 1, italics: true })],
    alignment: D.AlignmentType.CENTER, spacing: { before: 80, after: where ? 40 : 160 },
    keepNext: !!where,
  })];
  if (where) {
    out.push(new D.Paragraph({
      children: rich(where, { size: 20 }), alignment: D.AlignmentType.CENTER,
      spacing: { after: 160 },
    }));
  }
  return out;
}
const spacer = (after = 120) => new D.Paragraph({ children: [], spacing: { after } });
const pageBreak = () => new D.Paragraph({ children: [new D.PageBreak()] });

// ---------------------------------------------------------------------------
// tables
// ---------------------------------------------------------------------------
const thin = { style: D.BorderStyle.SINGLE, size: 4, color: RULE };
const cellBorders = { top: thin, bottom: thin, left: thin, right: thin };

function cell(content, width, o = {}) {
  const empty = content === null || content === undefined;
  const parts = empty ? [' '] : (Array.isArray(content) ? content : [content]);
  const run = { font: SANS, size: o.size || SMALL, bold: o.head || undefined };
  return new D.TableCell({
    width: { size: width, type: D.WidthType.DXA },
    borders: cellBorders,
    shading: (empty || o.head || o.fill)
      ? { type: D.ShadingType.CLEAR, color: 'auto', fill: empty ? PINK : (o.fill || HEAD_FILL) }
      : undefined,
    margins: { top: 50, bottom: 50, left: 70, right: 70 },
    verticalAlign: D.VerticalAlign.CENTER,
    columnSpan: o.span,
    children: parts.map((t) => new D.Paragraph({ children: rich(String(t), run),
      spacing: { after: 0, line: 250 }, keepNext: o.keep })),
  });
}

/** widths: column widths in DXA, summing to W. A cell given as null is an empty,
 *  pink cell: a value still to be filled in. */
function grid(widths, head, rows, o = {}) {
  const sum = widths.reduce((a, b) => a + b, 0);
  if (sum !== W) throw new Error(`table widths sum to ${sum}, not ${W}: ${head.join(' | ')}`);
  // a short table is kept on one page: every row but the last is tied to the next
  const short = rows.length <= 12;
  const mk = (cells, isHead, isLast) => new D.TableRow({
    tableHeader: isHead, cantSplit: true,
    children: cells.map((c, i) => cell(c, widths[i],
      { head: isHead, size: o.size, keep: short && !isLast })),
  });
  for (const r of rows) {
    if (r.length !== widths.length) throw new Error(`row length ${r.length} in table ${head[0]}`);
  }
  return new D.Table({
    width: { size: W, type: D.WidthType.DXA }, columnWidths: widths,
    rows: [mk(head, true, false), ...rows.map((r, i) => mk(r, false, i === rows.length - 1))],
  });
}
const caption = (label, title, rest = '', o = {}) => new D.Paragraph({
  children: [
    new D.TextRun({ text: `${label}. `, font: SANS, size: SMALL + 1, bold: true }),
    new D.TextRun({ text: title + (rest ? ' ' : ''), font: SANS, size: SMALL + 1, bold: true }),
    ...rich(rest, { font: SANS, size: SMALL + 1 }),
  ],
  spacing: { before: o.before ?? 80, after: o.after ?? 200, line: 260 },
  keepNext: o.keepNext, alignment: o.align,
});

/** A numbered table of the paper. */
function table(key, title, widths, head, rows, o = {}) {
  state.tabUsed.push(key);
  const out = [caption(T(key), title, o.lead || '', { keepNext: true, before: 160, after: 90 }),
    grid(widths, head, rows, o)];
  out.push(o.after ? P(o.after, { run: { font: SANS, size: SMALL }, after: 200, line: 250 })
    : spacer(200));
  return out;
}
/** A numbered table of the manual (Table M1, M2, ...). */
function mtable(title, widths, head, rows, o = {}) {
  state.mTab += 1;
  const out = [caption(`Table M${state.mTab}`, title, o.lead || '',
    { keepNext: true, before: 160, after: 90 }), grid(widths, head, rows, o)];
  out.push(o.after ? P(o.after, { run: { font: SANS, size: SMALL }, after: 200, line: 250 })
    : spacer(200));
  return out;
}

// ---------------------------------------------------------------------------
// figures
// ---------------------------------------------------------------------------
function pngSize(file) {
  const b = fs.readFileSync(file);
  return [b.readUInt32BE(16), b.readUInt32BE(20)];
}
function picture(file, widthPx, alt) {
  const [w, h] = pngSize(file);
  return new D.Paragraph({
    alignment: D.AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 40 },
    children: [new D.ImageRun({
      type: 'png', data: fs.readFileSync(file),
      transformation: { width: widthPx, height: Math.round((widthPx * h) / w) },
      altText: { title: alt, description: alt, name: path.basename(file) },
    })],
  });
}
const drawn = (name) => path.join(HERE, 'figures', `${name}.png`);
const bench = (name) => path.join(REPO, 'physical', 'figures', `${name}.png`);

/** A numbered figure of the paper that already exists. */
function figure(key, file, title, text, o = {}) {
  state.figUsed.push(key);
  state.figTitles[key] = title;
  return [picture(file, o.width || 600, title), caption(F(key), title, text)];
}
/** A numbered figure of the manual (Figure M1, M2, ...). */
function mfigure(file, title, text, o = {}) {
  state.mFig += 1;
  return [picture(file, o.width || 600, title), caption(`Figure M${state.mFig}`, title, text)];
}

/** A dashed, empty box. heightIn is the space reserved, in inches. */
function box(heightIn, paragraphs) {
  const dash = { style: D.BorderStyle.DASHED, size: 12, color: RED };
  return new D.Table({
    width: { size: W, type: D.WidthType.DXA }, columnWidths: [W],
    rows: [new D.TableRow({
      height: { value: Math.round(heightIn * 1440), rule: D.HeightRule.ATLEAST }, cantSplit: true,
      children: [new D.TableCell({
        width: { size: W, type: D.WidthType.DXA },
        borders: { top: dash, bottom: dash, left: dash, right: dash },
        margins: { top: 110, bottom: 110, left: 160, right: 160 },
        verticalAlign: D.VerticalAlign.TOP,
        children: paragraphs,
      })],
    })],
  });
}
/** A numbered figure of the paper that does not exist yet: a reserved space with
 *  its number, its proposed title and caption, and red instructions.
 *  kind: PHOTOGRAPH, SCREENSHOT or GRAPH. need: what must be in it.
 *  from / see: where it comes from and where the manual explains it. */
function figureSpace(key, kind, title, text, need, from, see, o = {}) {
  state.figUsed.push(key);
  state.figTitles[key] = title;
  const token = red(`Insert the ${kind.toLowerCase()} for Figure ${figNo(key)} here. ${need}`,
    from, see);
  const r = state.reds[token.slice(1, -1)];
  const inner = [
    new D.Paragraph({ children: [new D.TextRun({ text: `SPACE RESERVED FOR A ${kind}`,
      font: SANS, size: 18, bold: true, color: GREY })], spacing: { after: 80 } }),
    new D.Paragraph({ children: redRuns(`[${r.id}: ${r.text}]`), spacing: { after: 0, line: 260 } }),
  ];
  return [spacer(60), box(o.height || 2.6, inner),
    caption(F(key), title, text, { before: 100 })];
}
/** A reserved space for writing: red instruction, then room. */
function writeSpace(token, heightIn = 1.4) {
  const r = state.reds[token.slice(1, -1)];
  return [box(heightIn, [new D.Paragraph({ children: redRuns(`[${r.id}: ${r.text}]`, 20),
    spacing: { after: 0, line: 270 } })]), spacer(160)];
}

// ---------------------------------------------------------------------------
// the document
// ---------------------------------------------------------------------------
function makeDoc({ title, running, children }) {
  const hStyle = (id, name, size, before, after, color) => ({
    id, name, basedOn: 'Normal', next: 'Normal', quickFormat: true,
    run: { font: SANS, size, bold: true, color },
    paragraph: { spacing: { before, after }, keepNext: true,
      outlineLevel: Number(id.slice(-1)) - 1 },
  });
  return new D.Document({
    creator: 'Gayathri Nair', title, description: title,
    styles: {
      default: { document: { run: { font: SERIF, size: BODY } } },
      paragraphStyles: [
        hStyle('Heading1', 'Heading 1', 32, 360, 160, '12324F'),
        hStyle('Heading2', 'Heading 2', 25, 280, 110, '12324F'),
        hStyle('Heading3', 'Heading 3', 22, 200, 80, '000000'),
      ],
    },
    numbering: {
      config: [
        { reference: 'bul', levels: [{ level: 0, format: D.LevelFormat.BULLET, text: '•',
          alignment: D.AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 560, hanging: 280 } } } }] },
        { reference: 'num', levels: [{ level: 0, format: D.LevelFormat.DECIMAL, text: '%1.',
          alignment: D.AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 560, hanging: 360 } } } }] },
      ],
    },
    sections: [{
      properties: { page: { size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1300, left: 1440 } } },
      headers: { default: new D.Header({ children: [new D.Paragraph({
        children: [new D.TextRun({ text: running, font: SANS, size: 16, color: GREY })],
        border: { bottom: { style: D.BorderStyle.SINGLE, size: 4, color: RULE, space: 4 } },
      })] }) },
      footers: { default: new D.Footer({ children: [new D.Paragraph({
        alignment: D.AlignmentType.CENTER,
        children: [new D.TextRun({ children: ['Page ', D.PageNumber.CURRENT, ' of ',
          D.PageNumber.TOTAL_PAGES], font: SANS, size: 16, color: GREY })],
      })] }) },
      children,
    }],
  });
}

module.exports = {
  D, state, red, rich, redRuns, P, H1, H2, H3, bullets, numbered, note, code, formula, spacer,
  pageBreak, grid, table, mtable, caption, figure, mfigure, figureSpace, writeSpace, box,
  picture, drawn, bench, makeDoc, figNo, tabNo, F, T, REG, REPO, HERE, W, RED, SANS, SERIF,
  SMALL, BODY, GREY,
};
