/* Beginner-level presentation: what pycasa does, explained from zero.
 *
 * One idea per slide, a large visual on each, and an INPUT -> OUTPUT structure
 * for every step. The function used at each step is shown top-right. What to
 * say is in the speaker notes, not on the slide.
 *
 *   node scripts/build_beginner_deck.js [output.pptx]
 */
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const R = (f) => path.join(ROOT, "outputs", "report", f);
const OUT = process.argv[2] || path.join(ROOT, "pycasa_Beginner_Presentation.pptx");

/* ------------------------------------------------------------------ palette */
const INK = "0F1B2D";        // deep navy: dark slides, image frames, clinic series
const ORANGE = "F08A24";     // accent: matches the track colour in the animations
const TEXT = "1E293B";
const MUTED = "5B6B7F";
const PANEL = "EEF2F6";
const WHITE = "FFFFFF";
const SOFT = "C9D3E0";       // body text on dark slides
const GREEN = "16A34A";      // hand-marked boxes
const RED = "E5484D";        // software boxes

const W = 13.333, M = 0.6;
const FONT = "Calibri", MONO = "Consolas";

/* ------------------------------------------------------------------ helpers */
function imgSize(file) {
  const b = fs.readFileSync(file);
  if (b.slice(0, 3).toString() === "GIF") return { w: b.readUInt16LE(6), h: b.readUInt16LE(8) };
  if (b.slice(1, 4).toString() === "PNG") return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
  throw new Error("unknown image type: " + file);
}

/* Image fitted into a box (aspect kept), sitting on a dark rounded frame. */
function framed(pres, slide, file, x, y, w, h, align = "center") {
  const s = imgSize(file);
  let fw = w, fh = w * s.h / s.w;
  if (fh > h) { fh = h; fw = h * s.w / s.h; }
  const fx = align === "left" ? x : align === "right" ? x + w - fw : x + (w - fw) / 2;
  const fy = y;
  const pad = 0.07;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: fx - pad, y: fy - pad, w: fw + 2 * pad, h: fh + 2 * pad,
    fill: { color: INK }, line: { color: INK }, rectRadius: 0.1,
  });
  slide.addImage({ path: file, x: fx, y: fy, w: fw, h: fh });
  return { x: fx, y: fy, w: fw, h: fh };
}

function pill(pres, slide, text, x, y, w, opts = {}) {
  slide.addText(text, {
    shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.19,
    x, y, w, h: opts.h || 0.38,
    fill: { color: opts.fill || ORANGE }, line: { color: opts.fill || ORANGE },
    color: opts.color || WHITE, fontFace: opts.font || FONT,
    fontSize: opts.size || 13, bold: opts.bold !== false, charSpacing: opts.spacing ?? 1.5,
    align: "center", valign: "middle", margin: 0, isTextBox: true,
  });
}

function fnPill(pres, slide, code) {
  const w = Math.min(0.118 * code.length + 0.5, 6.2);
  pill(pres, slide, code, W - M - w, 0.36, w, {
    fill: PANEL, color: INK, font: MONO, size: 14, bold: false, spacing: 0, h: 0.44,
  });
}

function header(pres, slide, kicker, title) {
  slide.background = { color: WHITE };
  slide.addText(kicker, {
    x: M, y: 0.42, w: 6.5, h: 0.34, fontFace: FONT, fontSize: 14, bold: true,
    color: ORANGE, charSpacing: 3, margin: 0, isTextBox: true,
  });
  slide.addText(title, {
    x: M, y: 0.82, w: W - 2 * M, h: 0.8, fontFace: FONT, fontSize: 34, bold: true,
    color: TEXT, margin: 0, valign: "top", isTextBox: true,
  });
}

function arrow(pres, slide, x, yMid, w = 0.85) {
  slide.addShape(pres.shapes.RIGHT_ARROW, {
    x, y: yMid - 0.3, w, h: 0.6, fill: { color: ORANGE }, line: { color: ORANGE },
  });
}

function caption(slide, runs, y = 6.42, h = 0.5) {
  slide.addText(runs, {
    x: M, y, w: W - 2 * M, h, fontFace: FONT, fontSize: 17, color: TEXT,
    margin: 0, valign: "top", isTextBox: true,
  });
}

/* ------------------------------------------------------------------ deck */
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = "pycasa — measuring sperm movement from a microscope video";

/* 1. Title ---------------------------------------------------------------- */
{
  const s = pres.addSlide();
  s.background = { color: INK };
  s.addText("PYCASA  ·  DATA FUSION LAB", {
    x: M, y: 1.35, w: 6.8, h: 0.4, fontFace: FONT, fontSize: 15, bold: true,
    color: ORANGE, charSpacing: 4, margin: 0, isTextBox: true,
  });
  s.addText("Measuring sperm movement from a microscope video", {
    x: M, y: 1.9, w: 6.9, h: 2.3, fontFace: FONT, fontSize: 42, bold: true,
    color: WHITE, margin: 0, valign: "top", isTextBox: true,
  });
  s.addText("What the lab's pycasa software does, step by step", {
    x: M, y: 4.3, w: 6.9, h: 0.9, fontFace: FONT, fontSize: 21, color: SOFT,
    margin: 0, valign: "top", isTextBox: true,
  });
  s.addText("Prepared for Dr. Moshe Kam's research group  ·  NJIT  ·  September 2026", {
    x: M, y: 6.55, w: 7.5, h: 0.4, fontFace: FONT, fontSize: 13, color: "8A99AD",
    margin: 0, isTextBox: true,
  });
  framed(pres, s, R("11_one_cell.gif"), 8.1, 1.15, 4.6, 4.6);
  s.addText("One sperm cell, followed by the software", {
    x: 8.1, y: 5.9, w: 4.6, h: 0.4, fontFace: FONT, fontSize: 13, color: "8A99AD",
    align: "center", margin: 0, isTextBox: true,
  });
  s.addNotes(
    "Today I will show what the lab's software, pycasa, does. " +
    "It watches a microscope video of sperm cells and tells us how many there are and how well they swim. " +
    "On the right you can see one cell being followed by the software."
  );
}

/* 1b. What pycasa is: three parts, their options ------------------------------ */
{
  const s = pres.addSlide();
  header(pres, s, "WHAT IT IS", "What is pycasa?");
  s.addText("A free Python tool built by this lab for CASA: Computer-Assisted Semen Analysis.", {
    x: M, y: 1.55, w: W - 2 * M, h: 0.45, fontFace: FONT, fontSize: 19, color: MUTED,
    margin: 0, isTextBox: true,
  });
  const parts = [
    ["1", "Find the cells", "casa.detection",
      [["YOLOv5", false], ["YOLO26", true], ["Digital washing", false], ["Moving cells", false]]],
    ["2", "Follow the cells", "casa.tracking",
      [["SORT", true], ["DeepSORT", false], ["JPDAF  (the lab's own, 2017)", true]]],
    ["3", "Measure them", "casa.motility",
      [["Speeds  (VCL, VSL, VAP, ...)", true], ["% of cells moving", true],
       ["Cells per mL", true], ["Total cell count", true]]],
  ];
  const cw = 3.6, gap = (W - 2 * M - 3 * cw) / 2, cy = 2.35, ch = 3.75;
  parts.forEach(([n, name, code, opts], i) => {
    const x = M + i * (cw + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: cy, w: cw, h: ch, fill: { color: PANEL }, line: { color: PANEL }, rectRadius: 0.12,
    });
    s.addText(n, {
      shape: pres.shapes.OVAL, x: x + 0.25, y: cy + 0.25, w: 0.5, h: 0.5,
      fill: { color: INK }, line: { color: INK }, color: WHITE, fontFace: FONT,
      fontSize: 18, bold: true, align: "center", valign: "middle", margin: 0, isTextBox: true,
    });
    s.addText(name, {
      x: x + 0.9, y: cy + 0.25, w: cw - 1.1, h: 0.5, fontFace: FONT, fontSize: 21, bold: true,
      color: TEXT, valign: "middle", margin: 0, isTextBox: true,
    });
    s.addText(code, {
      x: x + 0.25, y: cy + 0.88, w: cw - 0.5, h: 0.36, fontFace: MONO, fontSize: 14,
      color: MUTED, margin: 0, isTextBox: true,
    });
    opts.forEach(([label, used], k) => {
      pill(pres, s, label, x + 0.25, cy + 1.42 + k * 0.54, cw - 0.5, {
        fill: used ? ORANGE : WHITE, color: used ? WHITE : TEXT, size: 15,
        bold: used, spacing: 0, h: 0.42,
      });
    });
    if (i < 2) arrow(pres, s, x + cw + gap / 2 - 0.2, cy + ch / 2, 0.4);
  });
  caption(s, [
    { text: "■ ", options: { color: ORANGE } },
    { text: "Orange", options: { bold: true } },
    { text: " = what we used in this presentation." },
  ], 6.4);
  s.addNotes(
    "pycasa is a free Python tool that this lab built. CASA means computer-assisted semen analysis: " +
    "a computer looks at the video instead of a person. " +
    "It has three parts. The first finds the cells, the second follows them, the third measures them. " +
    "Each part has several options to choose from. The orange ones are the ones I used, and the next slides show them."
  );
}

/* 2. The task: input and output --------------------------------------------- */
{
  const s = pres.addSlide();
  header(pres, s, "THE TASK", "One video in, clinic numbers out");
  fnPill(pres, s, "pc.io.load_default_data()");

  pill(pres, s, "INPUT", M, 1.85, 1.3);
  framed(pres, s, R("10_raw_video.gif"), M, 2.35, 5.2, 3.75, "left");
  s.addText("30-second video  ·  30 frames per second  ·  ~90 cells in view", {
    x: M, y: 6.2, w: 5.4, h: 0.6, fontFace: FONT, fontSize: 13, color: MUTED,
    margin: 0, valign: "top", isTextBox: true,
  });

  arrow(pres, s, 6.2, 4.2);

  const ox = 7.4;
  pill(pres, s, "OUTPUT", ox, 1.85, 1.5);
  const cards = [["42%", "swim fast"], ["23%", "swim slowly"],
                 ["9%", "wiggle in place"], ["26%", "don't move"]];
  cards.forEach(([num, lbl], i) => {
    const cx = ox + (i % 2) * 2.75, cy = 2.35 + Math.floor(i / 2) * 1.5;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: cx, y: cy, w: 2.55, h: 1.3, fill: { color: PANEL }, line: { color: PANEL }, rectRadius: 0.12,
    });
    s.addText(num, {
      x: cx + 0.2, y: cy + 0.1, w: 2.2, h: 0.72, fontFace: FONT, fontSize: 38, bold: true,
      color: INK, margin: 0, isTextBox: true,
    });
    s.addText(lbl, {
      x: cx + 0.2, y: cy + 0.8, w: 2.2, h: 0.4, fontFace: FONT, fontSize: 15, color: MUTED,
      margin: 0, isTextBox: true,
    });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: ox, y: 5.35, w: 5.3, h: 1.0, fill: { color: INK }, line: { color: INK }, rectRadius: 0.12,
  });
  s.addText([
    { text: "69 million", options: { fontSize: 30, bold: true, color: ORANGE } },
    { text: "   cells per mL", options: { fontSize: 17, color: WHITE } },
  ], { x: ox + 0.25, y: 5.35, w: 4.9, h: 1.0, fontFace: FONT, valign: "middle", margin: 0, isTextBox: true });
  s.addText("Target: the clinic's own report for this donor", {
    x: ox, y: 6.45, w: 5.3, h: 0.35, fontFace: FONT, fontSize: 13, color: MUTED, margin: 0, isTextBox: true,
  });
  s.addNotes(
    "The input is just a video. Thirty seconds, taken through a microscope, with about ninety cells in view. " +
    "The output we want is what a fertility clinic's machine reports: what share of cells swim fast, slowly, wiggle in place, or don't move, and how many cells there are. " +
    "For this donor we have the clinic's real report, so we can check the software against it."
  );
}

/* 3. How it works: three steps ---------------------------------------------- */
{
  const s = pres.addSlide();
  header(pres, s, "HOW IT WORKS", "Three steps: find, follow, measure");
  const steps = [
    ["10_raw_video.png", "The video", "What the microscope records"],
    ["02_gt_vs_yolo26.png", "1  ·  Find", "Draw a box around every cell"],
    ["03_sort_gt.png", "2  ·  Follow", "Link boxes into one path per cell"],
    ["12_speed_explained.png", "3  ·  Measure", "Turn each path into a speed"],
  ];
  const cw = 2.5, gap = (W - 2 * M - 4 * cw) / 3;
  steps.forEach(([img, name, desc], i) => {
    const x = M + i * (cw + gap);
    framed(pres, s, R(img), x, 2.0, cw, 2.0);
    s.addText(name, {
      x, y: 4.3, w: cw, h: 0.45, fontFace: FONT, fontSize: 20, bold: true,
      color: i ? ORANGE : INK, margin: 0, isTextBox: true,
    });
    s.addText(desc, {
      x, y: 4.8, w: cw, h: 0.8, fontFace: FONT, fontSize: 15, color: MUTED,
      margin: 0, valign: "top", isTextBox: true,
    });
    if (i < 3) arrow(pres, s, x + cw + gap / 2 - 0.22, 3.0, 0.44);
  });
  caption(s, [
    { text: "Output: ", options: { bold: true, color: ORANGE } },
    { text: "the same numbers a clinic's machine reports." },
  ], 6.2);
  s.addNotes(
    "The software works in three steps. " +
    "First it finds every cell in every frame. Then it follows each cell from frame to frame, so every cell gets a path. " +
    "Finally it measures how fast each cell moved along its path. The next three slides show one step each."
  );
}

/* 4. Step 1: find ------------------------------------------------------------ */
{
  const s = pres.addSlide();
  header(pres, s, "STEP 1  ·  FIND", "Find every cell in every frame");
  fnPill(pres, s, 'self.detection.yolo(yolo_model="yolo26")');
  pill(pres, s, "INPUT", M, 1.85, 1.3);
  framed(pres, s, R("10_raw_video.png"), M, 2.35, 4.9, 3.7, "left");
  arrow(pres, s, 6.24, 4.2);
  pill(pres, s, "OUTPUT", W - M - 4.63, 1.85, 1.5);
  framed(pres, s, R("02_gt_vs_yolo26.gif"), 7.83, 2.35, 4.9, 3.7, "right");
  caption(s, [
    { text: "■ ", options: { color: RED } }, { text: "Red", options: { bold: true } },
    { text: " = found by the software      " },
    { text: "■ ", options: { color: GREEN } }, { text: "Green", options: { bold: true } },
    { text: " = marked by a person      " },
    { text: "They agree on 99 of every 100 cells.", options: { bold: true, color: ORANGE } },
  ]);
  s.addNotes(
    "Step one: find the cells. The input is a single frame of the video. " +
    "The software, a detector called YOLO, draws a box around every sperm head. Those are the red boxes. " +
    "To check it, a person had also marked every cell by hand. Those are the green boxes. The software finds 99 of every 100 cells the person marked."
  );
}

/* 5. Step 2: follow ---------------------------------------------------------- */
{
  const s = pres.addSlide();
  header(pres, s, "STEP 2  ·  FOLLOW", "Follow each cell from frame to frame");
  fnPill(pres, s, "self.tracking.sort()");
  pill(pres, s, "INPUT", M, 1.85, 1.3);
  framed(pres, s, R("02_gt_vs_yolo26.png"), M, 2.35, 4.9, 3.7, "left");
  arrow(pres, s, 6.24, 4.2);
  pill(pres, s, "OUTPUT", W - M - 3.7, 1.85, 1.5);
  framed(pres, s, R("11_one_cell.gif"), W - M - 3.7, 2.35, 3.7, 3.7);
  caption(s, [
    { text: "Boxes in each frame  →  one path per cell. ", options: { bold: true } },
    { text: "Shown here: one cell, zoomed in. The software does this for all 90 at once." },
  ]);
  s.addNotes(
    "Step two: follow the cells. The input is the boxes from step one, frame by frame. " +
    "The software links the box in one frame to the same cell in the next frame. The result is a path for every cell. " +
    "On the right you see one cell, zoomed in, with its path drawn behind it. The software does this for all ninety cells at the same time."
  );
}

/* 6. Step 3: measure --------------------------------------------------------- */
{
  const s = pres.addSlide();
  header(pres, s, "STEP 3  ·  MEASURE", "Turn each path into a speed");
  fnPill(pres, s, "self.motility.kinematic_parameters()");
  pill(pres, s, "INPUT", M, 1.85, 1.3);
  framed(pres, s, R("12_speed_explained.png"), M, 2.35, 3.7, 3.7, "left");
  arrow(pres, s, 4.8, 4.2);
  pill(pres, s, "OUTPUT", 6.2, 1.85, 1.5);

  const rows = [
    { solid: true, label: "The real path", num: "56 µm per second", sub: "path speed (VCL)" },
    { solid: false, label: "Start to finish", num: "28 µm per second", sub: "straight-line speed (VSL)" },
  ];
  rows.forEach((r, i) => {
    const y = 2.45 + i * 1.75;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 6.2, y: y + 0.25, w: 1.1, h: 0.6, fill: { color: INK }, line: { color: INK }, rectRadius: 0.1,
    });
    s.addShape(pres.shapes.LINE, {
      x: 6.35, y: y + 0.55, w: 0.8, h: 0,
      line: r.solid ? { color: "FFA528", width: 4 } : { color: WHITE, width: 3, dashType: "dash" },
    });
    s.addText(r.label, {
      x: 7.6, y, w: 5.1, h: 0.42, fontFace: FONT, fontSize: 18, bold: true, color: TEXT, margin: 0, isTextBox: true,
    });
    s.addText(r.num, {
      x: 7.6, y: y + 0.42, w: 5.1, h: 0.62, fontFace: FONT, fontSize: 32, bold: true,
      color: r.solid ? ORANGE : INK, margin: 0, isTextBox: true,
    });
    s.addText(r.sub, {
      x: 7.6, y: y + 1.05, w: 5.1, h: 0.35, fontFace: FONT, fontSize: 14, color: MUTED, margin: 0, isTextBox: true,
    });
  });
  caption(s, [
    { text: "A zigzagging cell covers twice the distance it actually advances.", options: { bold: true } },
  ]);
  s.addNotes(
    "Step three: measure. The input is one cell's path. The orange line is where the cell really went. " +
    "The dashed line is just start to finish. This cell swam fifty-six micrometres per second along its path, but only moved forward at twenty-eight. " +
    "From speeds like these, the software sorts every cell into fast, slow, wiggling, or not moving."
  );
}

/* 7. Result vs the clinic ---------------------------------------------------- */
{
  const s = pres.addSlide();
  header(pres, s, "RESULT", "Does it match the clinic's machine?");
  fnPill(pres, s, "self.motility.casa_parameters()");
  s.addChart(pres.charts.BAR, [
    { name: "Clinic's machine", labels: ["Swim fast", "Swim slowly", "Wiggle in place", "Don't move"], values: [42, 23, 9, 26] },
    { name: "pycasa", labels: ["Swim fast", "Swim slowly", "Wiggle in place", "Don't move"], values: [37.8, 23.1, 0.8, 38.2] },
  ], {
    x: M, y: 1.85, w: 7.6, h: 4.35,
    barDir: "col", barGrouping: "clustered", barGapWidthPct: 55,
    chartColors: [INK, ORANGE],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 13, dataLabelColor: TEXT,
    dataLabelFormatCode: '0"%"',
    showLegend: true, legendPos: "t", legendFontSize: 14, legendFontFace: FONT, legendColor: TEXT,
    catAxisLabelColor: TEXT, catAxisLabelFontSize: 14, catAxisLabelFontFace: FONT,
    valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 50,
    valGridLine: { style: "none" }, catGridLine: { style: "none" },
  });
  s.addText("Fully automatic run on the whole 30-second video", {
    x: M, y: 6.2, w: 7.6, h: 0.35, fontFace: FONT, fontSize: 13, color: MUTED, margin: 0, isTextBox: true,
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 8.75, y: 2.1, w: 3.98, h: 3.2, fill: { color: PANEL }, line: { color: PANEL }, rectRadius: 0.12,
  });
  s.addText("Cell count", {
    x: 9.05, y: 2.3, w: 3.4, h: 0.4, fontFace: FONT, fontSize: 16, bold: true, color: MUTED, margin: 0, isTextBox: true,
  });
  s.addText("within 7%", {
    x: 9.05, y: 2.75, w: 3.4, h: 0.9, fontFace: FONT, fontSize: 44, bold: true, color: ORANGE, margin: 0, isTextBox: true,
  });
  s.addText([
    { text: "pycasa: 74 million / mL", options: { breakLine: true } },
    { text: "clinic: 69 million / mL" },
  ], {
    x: 9.05, y: 3.8, w: 3.4, h: 0.9, fontFace: FONT, fontSize: 16, color: TEXT, margin: 0, isTextBox: true,
  });
  caption(s, [
    { text: "Close overall. ", options: { bold: true } },
    { text: "It counts too many cells as \"don't move\": a false detection looks like a cell that isn't moving." },
  ], 6.62, 0.45);
  s.addNotes(
    "Here is the final answer next to the clinic's real report. " +
    "The number of cells is within seven percent, and the fast and slow groups are close. " +
    "The biggest difference is the 'don't move' group. When the software mistakes a speck of dirt for a cell, that speck never moves, so it gets counted as a cell that doesn't move."
  );
}

/* 8. SORT vs JPDAF ----------------------------------------------------------- */
{
  const s = pres.addSlide();
  header(pres, s, "COMPARING TWO WAYS TO FOLLOW", "SORT or JPDAF: which follows cells better?");
  fnPill(pres, s, "tracking.sort()   vs   tracking.jpdaf()");
  framed(pres, s, R("09_sort_vs_jpdaf.gif"), (W - 9.1) / 2, 1.85, 9.1, 4.05);
  caption(s, [
    { text: "Fewer, longer paths are better.", options: { bold: true, breakLine: true } },
    { text: "JPDAF (right) follows each cell about twice as long. SORT (left) loses cells when they touch, then restarts them." },
  ], 6.2, 0.8);
  s.addNotes(
    "The software can follow cells in two ways, SORT and JPDAF. JPDAF is the method from the lab's own 2017 paper. " +
    "Both got exactly the same boxes, over the whole thirty-second video. " +
    "Watch the paths build up. SORT, on the left, keeps losing cells when they touch and restarts them, so it ends with 401 short paths. JPDAF ends with 262 longer ones. Fewer, longer paths means it followed each cell better."
  );
}

/* 9. The problem we found ---------------------------------------------------- */
{
  const s = pres.addSlide();
  header(pres, s, "SOMETHING WE FOUND", "Same video, same program, two different answers");
  const cw = 4.2, gap = 1.1, x0 = (W - 2 * cw - gap) / 2;
  [
    { num: "77%", lbl: "run on its own", color: INK },
    { num: "80%", lbl: "run after another detector", color: ORANGE },
  ].forEach((c, i) => {
    const x = x0 + i * (cw + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: 2.0, w: cw, h: 2.7, fill: { color: PANEL }, line: { color: PANEL }, rectRadius: 0.14,
    });
    s.addText(c.num, {
      x, y: 2.2, w: cw, h: 1.3, fontFace: FONT, fontSize: 72, bold: true, color: c.color,
      align: "center", margin: 0, isTextBox: true,
    });
    s.addText("detection score", {
      x, y: 3.5, w: cw, h: 0.4, fontFace: FONT, fontSize: 16, color: MUTED, align: "center", margin: 0, isTextBox: true,
    });
    s.addText(c.lbl, {
      x, y: 3.92, w: cw, h: 0.45, fontFace: FONT, fontSize: 18, bold: true, color: TEXT, align: "center", margin: 0, isTextBox: true,
    });
  });
  s.addText("vs", {
    x: x0 + cw, y: 2.95, w: gap, h: 0.7, fontFace: FONT, fontSize: 26, bold: true, color: MUTED,
    align: "center", margin: 0, isTextBox: true,
  });
  s.addText([
    { text: "Why? ", options: { bold: true, color: ORANGE } },
    { text: "The program quietly switches between two methods for removing duplicate boxes, depending on what else was loaded first." },
  ], { x: x0, y: 5.0, w: 2 * cw + gap, h: 0.8, fontFace: FONT, fontSize: 18, color: TEXT, margin: 0, valign: "top", isTextBox: true });
  s.addText([
    { text: "Fix: ", options: { bold: true, color: ORANGE } },
    { text: "one line of code, " },
    { text: "import torchvision", options: { fontFace: MONO, color: INK } },
    { text: ", before running the detector." },
  ], { x: x0, y: 5.9, w: 2 * cw + gap, h: 0.5, fontFace: FONT, fontSize: 18, color: TEXT, margin: 0, isTextBox: true });
  s.addNotes(
    "While testing, we found a problem. We ran the exact same detector on the exact same video twice, on the same computer, and got two different scores: 77 and 80 percent. " +
    "The only difference was whether another detector had been run first. " +
    "The reason is hidden inside a shared library: it picks one of two methods for removing duplicate boxes, depending on what else is loaded. The fix is one line of code."
  );
}

/* 10. Summary ---------------------------------------------------------------- */
{
  const s = pres.addSlide();
  s.background = { color: INK };
  s.addText("In short", {
    x: M, y: 0.7, w: 7, h: 0.9, fontFace: FONT, fontSize: 40, bold: true, color: WHITE, margin: 0, isTextBox: true,
  });
  const points = [
    "A 30-second video becomes clinic-style numbers in three steps: find, follow, measure.",
    "JPDAF follows cells better than SORT, and the difference only shows on a long video.",
    "We found why results change between runs, and how to fix it with a single line of code.",
  ];
  points.forEach((t, i) => {
    const y = 2.0 + i * 1.4;
    s.addText(String(i + 1), {
      shape: pres.shapes.OVAL, x: M, y, w: 0.7, h: 0.7, fill: { color: ORANGE }, line: { color: ORANGE },
      fontFace: FONT, fontSize: 22, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0, isTextBox: true,
    });
    s.addText(t, {
      x: M + 1.0, y: y - 0.08, w: 6.6, h: 1.0, fontFace: FONT, fontSize: 21, color: WHITE,
      margin: 0, valign: "middle", isTextBox: true,
    });
  });
  framed(pres, s, R("05_full.png"), 8.6, 1.5, 4.13, 3.3);
  s.addText("Everything together: found cells, their paths, and the hand-marked check", {
    x: 8.6, y: 5.0, w: 4.13, h: 0.7, fontFace: FONT, fontSize: 13, color: "8A99AD",
    align: "center", margin: 0, valign: "top", isTextBox: true,
  });
  s.addNotes(
    "To sum up. The software turns a short video into the same kind of numbers a clinic reports, in three steps. " +
    "Of the two ways to follow cells, JPDAF works better, but you only see it on a long video. " +
    "And we found why the results could change from one run to the next, with a one-line fix. Thank you."
  );
}

pres.writeFile({ fileName: OUT }).then((f) => {
  const mb = fs.statSync(f).size / 1e6;
  console.log(`written: ${f}  (${mb.toFixed(1)} MB, ${pres.slides.length} slides)`);
});
