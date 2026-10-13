// Builds W8/output/Dams_Blocks_2_4_6.docx: the Block 6 "characteristics of the proposed dams" table for Blocks 2, 4 and 6.
// Data: W8/data/dams_blocks_2_4_6.csv (one row per dam; the note column holds the derivation).
const fs = require("fs"), path = require("path");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, AlignmentType, ShadingType,
        BorderStyle, HeadingLevel, LevelFormat, VerticalAlign } = require("docx");
const root = path.resolve(__dirname, "..");
const rows = fs.readFileSync(path.join(root, "data", "dams_blocks_2_4_6.csv"), "utf8").trim().split(/\r?\n/).slice(1).map(l => {
  const c = l.split(","); return { block: +c[0], dam: c[1], label: c[2], type: c[3], h: c[4], L: c[5], fsl: c[6], cap: c[7], note: c.slice(8).join(",") };
});
const FONT = "Arial", SZ = 20; // 10 pt
const fmt = n => Number(n).toLocaleString("en-US");
const cap1 = n => Number(n).toFixed(1);
const P = (text, o = {}) => new Paragraph({ spacing: { after: o.after ?? 120, before: o.before ?? 0 }, alignment: o.align, keepNext: o.keepNext,
  children: [new TextRun({ text, font: FONT, size: o.size ?? SZ, bold: o.bold, italics: o.italics })] });
const border = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
const borders = { top: border, bottom: border, left: border, right: border };
const W = [2300, 1400, 1350, 1350, 1250, 1350]; // DXA, sum 9000
const cell = (text, w, o = {}) => new TableCell({ width: { size: w, type: WidthType.DXA }, borders, verticalAlign: VerticalAlign.CENTER,
  shading: o.head ? { type: ShadingType.CLEAR, fill: "D9D9D9", color: "auto" } : undefined,
  margins: { top: 60, bottom: 60, left: 80, right: 80 },
  children: [new Paragraph({ alignment: o.align ?? AlignmentType.CENTER, spacing: { after: 0 },
    children: [new TextRun({ text, font: FONT, size: o.head ? 18 : SZ, bold: o.head || o.bold })] })] });
const header = ["Dam Name", "Dam Type", "Height above wadi (m)", "Crest Length (m)", "FSL (m a.s.l.)", "Reservoir Capacity (MCM)"];
function damTable(block) {
  const data = rows.filter(r => r.block === block);
  return new Table({ width: { size: 9000, type: WidthType.DXA }, columnWidths: W, alignment: AlignmentType.CENTER,
    rows: [new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, W[i], { head: true })) }),
      ...data.map(r => new TableRow({ cantSplit: true, children: [
        cell(r.label, W[0], { align: AlignmentType.LEFT, bold: true }), cell(r.type, W[1]), cell(r.h, W[2]), cell(fmt(r.L), W[3]), cell(r.fsl, W[4]), cell(cap1(r.cap), W[5])] }))] });
}
const caption = (n, t) => P(`Table ${n} - Characteristics of the proposed dams in Block ${t}`, { bold: true, align: AlignmentType.CENTER, keepNext: true, before: 240, after: 120 });
const note = t => P(t, { italics: true, size: 18, after: 40 });
const bullets = { config: [{ reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
  style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] };
const B = text => new Paragraph({ numbering: { reference: "b", level: 0 }, spacing: { after: 80 }, children: [new TextRun({ text, font: FONT, size: SZ })] });
const H = (text, lvl) => new Paragraph({ heading: lvl, spacing: { before: lvl === HeadingLevel.HEADING_1 ? 0 : 360, after: 200 },
  children: [new TextRun({ text, font: FONT, size: lvl === HeadingLevel.HEADING_1 ? 32 : 26, bold: true, color: "000000" })] });
const children = [
  H("Characteristics of the proposed dams - Blocks 2, 4 and 6", HeadingLevel.HEADING_1),
  P("The three tables below list the proposed dams of the Renardet blocks in one layout: dam type, height above the wadi bed, crest length, full supply level and reservoir capacity at full supply level. " +
    "Height above wadi is the crest elevation minus the lowest ground along the dam axis; crest length is the length of the dam axis, closure sections included, dikes excluded. " +
    "The Block 6 table is the one issued with the Block 6 masterplan; the Block 4 and Block 2 tables are built on the same definitions from the current dam axes, levels and reservoir capacities."),
  caption(1, "2"), damTable(2),
  note("Dam types in Block 2 are not yet decided; the two dams are second-priority sites of the approved list of priority dams (November 2024). Crest levels 99 m (Bidah 03) and 224 m (Faydh 01) a.s.l."),
  caption(2, "4"), damTable(4),
  note("** Upgradation of the existing dam. GFRD+RCC: embankment with an RCC section across the wadi; the type of Sakhin 08 is not yet decided. Sarami 03 and Sakhin 08 carry an additional dike of about 480 m and 940 m."),
  caption(3, "6"), damTable(6),
  note("* Rehabilitation of the existing dam. ** Upgradation of the existing dam."),
  P("Dam types: FSHD - faced symmetrical hardfill dam; GFRD - geomembrane-faced rockfill (granular fill) dam; RCC - roller-compacted concrete gravity dam.", { before: 160 }),
  H("Basis and sources (internal - not for the report)", HeadingLevel.HEADING_2),
  P("Block 6: the dam team's details sheet, 07-Structures\\03-Dam Design\\01-Block 6 Dams\\Block 6 Dams Details.xlsx, reproduced without change; it is Table 34 of the Block 6 masterplan report and the table still sitting in the Block 4 masterplan draft. Their heights and crest lengths come from the axis profiles on the 2 m DEM (Characteristics\\*.dxf): crest minus the lowest profile point, and the axis length."),
  P("Block 4: FSL and reservoir capacity from the dam team's Block 4 Dams Details.xlsx (identical to the hydraulic copy in 04-Hydraulic\\00 Data\\Dams\\Block 04); dam type from their Chracteristics\\Block 4 Dams.xlsx; height and crest length derived here from their Chracteristics\\*.dxf profiles with the Block 6 definition (the Block 6 values re-derived the same way agree within 1 m and 1 %, Taww UP excepted: 20.1 m on the profile against 17 m in the sheet). The Block 4 hydrology report (R4) states the height as crest minus the reservoir bed of the EAV curve, which differs from these by at most 1 m."),
  P("Block 2: axes and reservoir polygons of January 2025 (04-Hydraulic\\00 Data\\SHP\\1st_2nd_Priority_DAM_AXIS_ART_REN 08.01.2025), profiled on the 2 m DEM (13-Study and Design\\01-FS and PD\\00-General\\01-Topography\\NSA_Batinah_2m.tif). The axis ends sit at the crest level and the reservoir polygon boundary at the FSL, which confirms the levels of the 2023 feasibility ranking (07-Structures\\02-Potential Dam Sites\\02-Feasibility\\02-Ranking Matrix\\Dam site Characteristics.xlsx: FSL 94 / crest 99 and FSL 219 / crest 224). Capacity is the volume below FSL inside the reservoir polygon. No dam design exists yet: the folders 07-Structures\\03-Dam Design\\03-Block 2 Dams, Bidah 03 and Faydh 01 are empty, the Block 02 HMS dam model has sinks at the two sites and no reservoirs, and the March 2025 feasibility slides for Bidah and Faydh carry only the general sheet. The dam team's tentative cost sheet (07-Structures\\Ad-hoc Reports\\03-Tentative Costs of Dams) rounds them to 25 m / 1,300 m (listed there as Bidah 01) and 50 m / 900 m, at 10.3 and 19.7 million OMR."),
  P("Per-dam derivation notes:", { bold: true, before: 120 }),
  ...rows.filter(r => r.note).map(r => B(`${r.label.replace(/\*+$/, "")}: ${r.note}.`)),
];
const doc = new Document({ numbering: bullets, styles: { default: { document: { run: { font: FONT, size: SZ } } } },
  sections: [{ properties: { page: { margin: { top: 1134, bottom: 1134, left: 1418, right: 1418 } } }, children }] });
Packer.toBuffer(doc).then(b => { const out = path.join(root, "output", "Dams_Blocks_2_4_6.docx"); fs.writeFileSync(out, b); console.log("wrote", out, b.length, "bytes"); });
