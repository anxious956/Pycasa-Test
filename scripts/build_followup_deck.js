/* Follow-up presentation: the two questions the professor asked after the first deck.
 *
 *   1) How do the detectors compare?       (all five, same frames, same hand-marked answer key)
 *   2) What happens when two cells touch?  (SORT vs JPDAF on one collision, plus the count over all of them)
 *
 * Same style as build_beginner_deck.js: one idea per slide, a big animation on
 * each, the function used top-right, what to say in the speaker notes.
 * Numbers are read from outputs/report/14_detectors.json and 13_collision.json,
 * both written by scripts/make_followup_visuals.py.
 *
 *   node scripts/build_followup_deck.js [output.pptx]
 */
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const R = (f) => path.join(ROOT, "outputs", "report", f);
const OUT = process.argv[2] || path.join(ROOT, "pycasa_Followup_Presentation.pptx");
const DET = JSON.parse(fs.readFileSync(R("14_detectors.json")));
const COL = JSON.parse(fs.readFileSync(R("13_collision.json")));
const STEP8 = JSON.parse(fs.readFileSync(path.join(ROOT, "outputs", "step8_full_clip.json")));
const fmt = (n) => n.toLocaleString("en-US");

/* ------------------------------------------------------------------ palette */
const INK = "0F1B2D";
const ORANGE = "F08A24";
const CYAN = "40C8FF";       // second track colour in the animations
const TEXT = "1E293B";
const MUTED = "5B6B7F";
const PANEL = "EEF2F6";
const WHITE = "FFFFFF";
const SOFT = "C9D3E0";
const GREEN = "16A34A";
const RED = "E5484D";

const W = 13.333, M = 0.6;
const FONT = "Calibri", MONO = "Consolas";

/* ------------------------------------------------------------------ helpers */
function imgSize(file) {
  const b = fs.readFileSync(file);
  if (b.slice(0, 3).toString() === "GIF") return { w: b.readUInt16LE(6), h: b.readUInt16LE(8) };
  if (b.slice(1, 4).toString() === "PNG") return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
  throw new Error("unknown image type: " + file);
}

function framed(pres, slide, file, x, y, w, h, align = "center") {
  const s = imgSize(file);
  let fw = w, fh = w * s.h / s.w;
  if (fh > h) { fh = h; fw = h * s.w / s.h; }
  const fx = align === "left" ? x : align === "right" ? x + w - fw : x + (w - fw) / 2;
  const pad = 0.07;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: fx - pad, y: y - pad, w: fw + 2 * pad, h: fh + 2 * pad,
    fill: { color: INK }, line: { color: INK }, rectRadius: 0.1,
  });
  slide.addImage({ path: file, x: fx, y, w: fw, h: fh });
  return { x: fx, y, w: fw, h: fh };
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
  const w = Math.min(0.118 * code.length + 0.5, 6.4);
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

function caption(slide, runs, y = 6.42, h = 0.5) {
  slide.addText(runs, {
    x: M, y, w: W - 2 * M, h, fontFace: FONT, fontSize: 17, color: TEXT,
    margin: 0, valign: "top", isTextBox: true,
  });
}

function card(pres, slide, x, y, w, h, big, label, color = INK) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, fill: { color: PANEL }, line: { color: PANEL }, rectRadius: 0.12,
  });
  slide.addText(big, {
    x: x + 0.25, y: y + 0.15, w: w - 0.5, h: h * 0.55, fontFace: FONT, fontSize: 40, bold: true,
    color, margin: 0, valign: "middle", isTextBox: true,
  });
  slide.addText(label, {
    x: x + 0.25, y: y + h * 0.62, w: w - 0.5, h: h * 0.35, fontFace: FONT, fontSize: 14,
    color: MUTED, margin: 0, valign: "top", isTextBox: true,
  });
}

/* ------------------------------------------------------------------ data */
const ORDER = ["yolov5", "yolo26", "moving_cells", "digital_washing", "urbano"];
const LABEL = { yolov5: "YOLOv5", yolo26: "YOLO26", moving_cells: "Moving cells",
                digital_washing: "Digital washing", urbano: "Urbano" };
const CALL = { yolov5: "yolo(yolo_model='yolov5')", yolo26: "yolo(yolo_model='yolo26')",
               moving_cells: "detect_moving_cells()", digital_washing: "digital_washing()",
               urbano: "urbano_detection()" };
const f1 = (n) => DET[n].assessment.F1, prec = (n) => DET[n].assessment.precision, rec = (n) => DET[n].assessment.recall;
const sortKept = COL.stats.sort, jpdafKept = COL.stats.jpdaf;
const pct = (s) => Math.round(100 * s.kept / s.n);
const demo = COL.demo, swap = COL["13b_swap"], brk = COL["13c_break"];
const ids = (ev, b) => ev[b].ids.map((t) => t.replace("t", "")).join(", ");

/* ------------------------------------------------------------------ deck */
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = "pycasa — two follow-up questions";

/* 1. Title ---------------------------------------------------------------- */
{
  const s = pres.addSlide();
  s.background = { color: INK };
  s.addText("PYCASA  ·  DATA FUSION LAB", {
    x: M, y: 1.35, w: 6.8, h: 0.4, fontFace: FONT, fontSize: 15, bold: true,
    color: ORANGE, charSpacing: 4, margin: 0, isTextBox: true,
  });
  s.addText("Two follow-up questions", {
    x: M, y: 1.9, w: 6.9, h: 1.2, fontFace: FONT, fontSize: 42, bold: true,
    color: WHITE, margin: 0, valign: "top", isTextBox: true,
  });
  s.addText([
    { text: "1  ", options: { bold: true, color: ORANGE } },
    { text: "How do the two YOLO versions compare?", options: { breakLine: true } },
    { text: "2  ", options: { bold: true, color: ORANGE } },
    { text: "When two cells touch, does the software keep them apart?" },
  ], {
    x: M, y: 3.3, w: 6.9, h: 1.6, fontFace: FONT, fontSize: 21, color: SOFT,
    margin: 0, valign: "top", paraSpaceAfter: 8, isTextBox: true,
  });
  s.addText("Dr. Moshe Kam's research group  ·  NJIT  ·  October 2026", {
    x: M, y: 6.55, w: 7.5, h: 0.4, fontFace: FONT, fontSize: 13, color: "8A99AD", margin: 0, isTextBox: true,
  });
  framed(pres, s, R("13c_break_sort_vs_jpdaf.gif"), 7.9, 1.6, 4.85, 4.0);
  s.addText("One cell followed by SORT (left) and JPDAF (right)", {
    x: 7.9, y: 5.45, w: 4.85, h: 0.4, fontFace: FONT, fontSize: 13, color: "8A99AD",
    align: "center", margin: 0, isTextBox: true,
  });
  s.addNotes(
    "Last time you asked two things. First, how the two YOLO versions compare at finding cells. " +
    "Second, what happens to the tracking when two cells touch. This short deck answers both with pictures."
  );
}

/* 2. Recap: what pycasa does, what we ran for this deck -------------------------- */
{
  const s = pres.addSlide();
  header(pres, s, "WHERE WE ARE", "pycasa in one picture, and what we ran this time");
  s.addText([
    { text: "pycasa ", options: { bold: true } },
    { text: "is the lab's Python tool for computer-assisted semen analysis. " },
    { text: "Input: ", options: { bold: true } },
    { text: "a 30-second clinic video (899 frames, about 90 cells in view) plus every cell marked by hand, as the answer key." },
  ], {
    x: M, y: 1.6, w: W - 2 * M, h: 0.7, fontFace: FONT, fontSize: 16, color: TEXT, margin: 0, valign: "top", isTextBox: true,
  });
  const cols = [
    ["1", "Find the cells", "casa.detection", ["yolo(yolo_model='yolov5')", "yolo(yolo_model='yolo26')"],
      "This time: the two YOLO versions, head to head on the whole video.", true],
    ["2", "Follow the cells", "casa.tracking", ["sort()", "jpdaf()"],
      "This time: what each tracker does when two cells touch.", true],
    ["3", "Measure them", "casa.motility", ["kinematic_parameters()", "casa_parameters()"],
      "Last time: speeds per cell and the clinic-style numbers.", false],
  ];
  const cw = 3.85, gap = (W - 2 * M - 3 * cw) / 2, cy = 2.5, ch = 3.75;
  cols.forEach(([n, name, mod, fns, note, now], i) => {
    const x = M + i * (cw + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: cy, w: cw, h: ch, fill: { color: PANEL }, line: { color: PANEL }, rectRadius: 0.12,
    });
    s.addText(n, {
      shape: pres.shapes.OVAL, x: x + 0.25, y: cy + 0.25, w: 0.5, h: 0.5,
      fill: { color: now ? ORANGE : INK }, line: { color: now ? ORANGE : INK }, color: WHITE, fontFace: FONT,
      fontSize: 18, bold: true, align: "center", valign: "middle", margin: 0, isTextBox: true,
    });
    s.addText(name, {
      x: x + 0.9, y: cy + 0.25, w: cw - 1.1, h: 0.5, fontFace: FONT, fontSize: 21, bold: true,
      color: TEXT, valign: "middle", margin: 0, isTextBox: true,
    });
    s.addText(mod, {
      x: x + 0.25, y: cy + 0.9, w: cw - 0.5, h: 0.32, fontFace: MONO, fontSize: 13, color: MUTED, margin: 0, isTextBox: true,
    });
    fns.forEach((f, k) => {
      pill(pres, s, f, x + 0.25, cy + 1.32 + k * 0.5, cw - 0.5, {
        fill: WHITE, color: TEXT, font: MONO, size: 12, bold: false, spacing: 0, h: 0.4,
      });
    });
    s.addText(note, {
      x: x + 0.25, y: cy + 2.45, w: cw - 0.5, h: 1.15, fontFace: FONT, fontSize: 14, bold: now,
      color: now ? TEXT : MUTED, margin: 0, valign: "top", isTextBox: true,
    });
    if (i < 2) {
      s.addShape(pres.shapes.RIGHT_ARROW, {
        x: x + cw + gap / 2 - 0.16, y: cy + ch / 2 - 0.22, w: 0.32, h: 0.44, fill: { color: ORANGE }, line: { color: ORANGE },
      });
    }
  });
  caption(s, [
    { text: "Orange = the two parts this deck is about. ", options: { bold: true } },
    { text: "Both trackers were run on the hand-marked boxes, so the tracking is judged on its own, not on the detector's mistakes." },
  ], 6.5, 0.6);
  s.addNotes(
    "A quick reminder of where we are. pycasa works in three steps: find the cells in every frame, follow each cell from frame to frame, and measure how it moves. " +
    "The input is the same 30-second clinic video as last time, with every cell marked by hand so we can check the software. " +
    "Today is about the first two steps. For finding cells, we compare the two YOLO versions. For following cells, we look at what SORT and JPDAF do when two cells touch. " +
    "The trackers ran on the hand-marked boxes, so what you will see is the tracking itself, not detector mistakes."
  );
}

/* 3. Q1: YOLOv5 vs YOLO26, close up, and the whole-video counts ------------- */
{
  const s = pres.addSlide();
  header(pres, s, "QUESTION 1  ·  THE TWO YOLO VERSIONS", "YOLOv5 misses cells; YOLO26 draws extra boxes");
  fnPill(pres, s, "casa.detection.yolo(yolo_model=...)");
  framed(pres, s, R("14_yolov5_vs_yolo26.gif"), M, 1.85, 7.9, 3.25, "left");
  const v5 = STEP8.yolov5.detection, y26 = STEP8.yolo26.detection;
  const total = v5.tp + v5.fn;                       // every hand-marked cell in every frame
  const cx = 8.95, cw = 3.78;
  card(pres, s, cx, 1.85, cw, 1.5, `${Math.round(v5.F1)}%`, "YOLOv5  ·  detection score, whole video");
  card(pres, s, cx, 3.5, cw, 1.5, `${Math.round(y26.F1)}%`, "YOLO26  ·  detection score, whole video", ORANGE);
  s.addText([
    { text: "The whole 30-second video: ", options: { bold: true } },
    { text: `${STEP8.yolo26.frames_loaded} frames, ${fmt(total)} hand-marked cells (about ${Math.round(total / STEP8.yolo26.frames_loaded)} in every frame).`, options: { breakLine: true } },
    { text: "YOLOv5 ", options: { bold: true } },
    { text: `found ${fmt(v5.tp)} of them, missed ${fmt(v5.fn)}, and drew ${fmt(v5.fp)} wrong boxes.`, options: { breakLine: true } },
    { text: "YOLO26 ", options: { bold: true } },
    { text: `found ${fmt(y26.tp)} of them, missed ${fmt(y26.fn)}, and drew ${fmt(y26.fp)} wrong boxes.` },
  ], {
    x: M, y: 5.3, w: W - 2 * M, h: 1.15, fontFace: FONT, fontSize: 16, color: TEXT, margin: 0,
    valign: "top", paraSpaceAfter: 3, isTextBox: true,
  });
  caption(s, [
    { text: "Which is better? ", options: { bold: true, color: ORANGE } },
    { text: "YOLO26 almost never misses a cell, which matters for counting. Its extra boxes are the price: they show up later as \"cells that don't move\"." },
  ], 6.55, 0.7);
  s.addNotes(
    "The same region, zoomed in, with the two YOLO versions side by side. " +
    `Over the whole video a person marked ${fmt(total)} cells, frame by frame; that is about ${Math.round(total / STEP8.yolo26.frames_loaded)} cells in every frame. ` +
    `YOLOv5 found ${fmt(v5.tp)} of them and missed ${fmt(v5.fn)}, about one in four, but most of the boxes it drew are real cells. ` +
    `YOLO26 found ${fmt(y26.tp)} and missed only ${fmt(y26.fn)}, but it drew ${fmt(y26.fp)} wrong boxes, roughly one box in three. ` +
    "For counting cells, not missing any is the more important of the two. The extra boxes are the thing to fix: they get tracked as cells that never move."
  );
}

/* (unused) a clustered chart of the detector scores ---------------------------- */
function scoreSlide(data, kicker, title, footnote, notes) {
  const s = pres.addSlide();
  header(pres, s, kicker, title);
  fnPill(pres, s, "casa.assessment.evaluate_detections()");
  const g = (n, k) => Math.round(data[n].assessment[k]);
  const labels = ORDER.map((n) => LABEL[n]);
  s.addChart(pres.charts.BAR, [
    { name: "Detection score (F1)", labels, values: ORDER.map((n) => g(n, "F1")) },
    { name: "Cells found (of 100)", labels, values: ORDER.map((n) => g(n, "recall")) },
    { name: "Boxes that are right (of 100)", labels, values: ORDER.map((n) => g(n, "precision")) },
  ], {
    x: M, y: 1.85, w: 8.4, h: 4.45,
    barDir: "col", barGrouping: "clustered", barGapWidthPct: 60,
    chartColors: [ORANGE, INK, "9AA8B8"],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 11, dataLabelColor: TEXT,
    showLegend: true, legendPos: "t", legendFontSize: 13, legendFontFace: FONT, legendColor: TEXT,
    catAxisLabelColor: TEXT, catAxisLabelFontSize: 13, catAxisLabelFontFace: FONT,
    valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 110,
    valGridLine: { style: "none" }, catGridLine: { style: "none" },
  });
  const px = 9.35, pw = W - M - px;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: px, y: 1.85, w: pw, h: 4.45, fill: { color: PANEL }, line: { color: PANEL }, rectRadius: 0.12,
  });
  const timeRows = ORDER.filter((n) => data[n].seconds != null);
  s.addText([
    { text: "How to read it", options: { bold: true, fontSize: 15, color: MUTED, breakLine: true } },
    { text: "Cells found: ", options: { bold: true } },
    { text: "of 100 hand-marked cells, how many got a box.", options: { breakLine: true } },
    { text: "Boxes right: ", options: { bold: true } },
    { text: "of 100 boxes the software drew, how many sit on a real cell.", options: { breakLine: true } },
    { text: "Score: ", options: { bold: true } },
    { text: "one number that balances the two. 100 = every cell found, no wrong boxes.", options: { breakLine: timeRows.length > 0 } },
    ...(timeRows.length ? [
      { text: " ", options: { fontSize: 6, breakLine: true } },
      { text: `Time for ${data[timeRows[0]].frames_loaded || 100} frames`, options: { bold: true, fontSize: 15, color: MUTED, breakLine: true } },
      ...timeRows.map((n, i) => ({ text: `${LABEL[n]}: ${Math.round(data[n].seconds)} s`, options: { breakLine: i < timeRows.length - 1 } })),
    ] : []),
  ], {
    x: px + 0.25, y: 2.0, w: pw - 0.5, h: 4.2, fontFace: FONT, fontSize: 13, color: TEXT,
    margin: 0, valign: "top", paraSpaceAfter: 3, isTextBox: true,
  });
  caption(s, footnote, 6.5, 0.8);
  s.addNotes(notes);
}

/* 5. Q2: one cell, SORT cuts the path, JPDAF keeps it ---------------------- */
{
  const s = pres.addSlide();
  header(pres, s, "QUESTION 2  ·  FOLLOWING ONE CELL", "SORT cuts the path in two; JPDAF keeps it whole");
  fnPill(pres, s, "casa.tracking.sort()   vs   casa.tracking.jpdaf()");
  framed(pres, s, R("13c_break_user.gif"), (W - 8.6) / 2, 1.8, 8.6, 4.4);
  caption(s, [
    { text: "Each colour is one path: the software's idea of \"the same cell\". ", options: { bold: true } },
    { text: "The blue cell swims down and touches the yellow one. ", options: {} },
    { text: "SORT", options: { bold: true } },
    { text: ` loses it at the touch (frame ${brk.f0}): path 1 stops, and at frame ${brk.f1} a new path 2 starts on the same cell. One cell, two paths. `, options: {} },
    { text: "JPDAF", options: { bold: true } },
    { text: " keeps path 1 all the way." },
  ], 6.35, 0.9);
  s.addNotes(
    "This is one cell from the video, zoomed in, with the same frames on both sides, slowed down. " +
    "Each colour is one ID. An ID is the name the software gives a cell so it can say 'this is still the same cell' from one frame to the next. " +
    "The blue cell swims down and touches the yellow cell. " +
    "On the left, SORT: at the moment they touch, it loses the blue cell. A few frames later it picks it up again, but as a new path, path 2, so the path is cut in two. " +
    "On the right, JPDAF: one ID, one path, all the way through. " +
    "Both trackers ran on the hand-marked boxes, so the only difference here is the tracking itself."
  );
}

/* 5b. Q2: a second cell, same thing ------------------------------------------ */
{
  const s = pres.addSlide();
  header(pres, s, "QUESTION 2  ·  A SECOND EXAMPLE", "Same thing on another cell");
  fnPill(pres, s, "casa.tracking.sort()   vs   casa.tracking.jpdaf()");
  framed(pres, s, R("13d_break0_user.gif"), (W - 8.6) / 2, 1.8, 8.6, 4.4);
  caption(s, [
    { text: "SORT", options: { bold: true } },
    { text: " drops the cell at frame 210 and starts path 2 on it at frame 213. ", options: {} },
    { text: "JPDAF", options: { bold: true } },
    { text: " follows it as one path from frame 0 to frame 708.  Over the whole video SORT restarted a path 13 times where JPDAF did not; the reverse never happened." },
  ], 6.35, 0.9);
  s.addNotes(
    "A second cell, same story. SORT drops it for a few frames and then picks it up as a new path. JPDAF never lets go. " +
    "We looked for every case like this in the video: thirteen times SORT restarted a path where JPDAF carried on, and never the other way round."
  );
}

/* 6. Q2: frame by frame ------------------------------------------------------ */
{
  const s = pres.addSlide();
  header(pres, s, "QUESTION 2  ·  FRAME BY FRAME", "The first cell again: before, the cut, after");
  framed(pres, s, R("13c_break_strip.png"), M, 1.8, 7.3, 4.9, "left");
  const bx = 8.35, bw = W - M - bx;
  const rows = [
    ["SORT", INK, `IDs ${ids(brk, "sort")}`, `The track stops at frame ${brk.f0} and a new one starts at frame ${brk.f1}. One cell, two paths, and the speed over the gap is lost.`],
    ["JPDAF", ORANGE, `ID ${ids(brk, "jpdaf")}`, "One ID survives the pass. One cell, one path."],
  ];
  rows.forEach(([name, col, idtxt, text], i) => {
    const y = 1.85 + i * 2.45;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: bx, y, w: bw, h: 2.25, fill: { color: PANEL }, line: { color: PANEL }, rectRadius: 0.12,
    });
    s.addText(name, {
      x: bx + 0.25, y: y + 0.18, w: bw - 0.5, h: 0.45, fontFace: FONT, fontSize: 22, bold: true, color: col,
      margin: 0, isTextBox: true,
    });
    s.addText(idtxt, {
      x: bx + 0.25, y: y + 0.65, w: bw - 0.5, h: 0.35, fontFace: MONO, fontSize: 13, color: MUTED,
      margin: 0, isTextBox: true,
    });
    s.addText(text, {
      x: bx + 0.25, y: y + 1.05, w: bw - 0.5, h: 1.1, fontFace: FONT, fontSize: 15, color: TEXT,
      margin: 0, valign: "top", isTextBox: true,
    });
  });
  s.addText(`Frames ${brk.f0 - 40} to ${brk.f1 + 40} of the video  ·  thin grey lines are other cells`, {
    x: M, y: 6.8, w: 7.3, h: 0.35, fontFace: FONT, fontSize: 12, color: MUTED, margin: 0, isTextBox: true,
  });
  s.addNotes(
    "The same cell as three still pictures: before, at the cut, and after. Top row SORT, bottom row JPDAF. " +
    "In the middle picture, SORT has already lost the cell: the red X is where its track stopped, and there is no circle on the cell. " +
    "In the right picture the cell is back, but as a new ID in a new colour. JPDAF keeps the same ID in all three. " +
    "That is the whole difference: whether the software remembers that it is the same cell."
  );
}

/* 7. Q2: two cells touch ------------------------------------------------------ */
{
  const s = pres.addSlide();
  header(pres, s, "QUESTION 2  ·  TWO CELLS TOUCH", "Two cells touch: does the software keep them apart?");
  fnPill(pres, s, "casa.tracking.sort()   vs   casa.tracking.jpdaf()");
  framed(pres, s, R("13_collision_sort_vs_jpdaf.gif"), (W - 8.0) / 2, 1.8, 8.0, 4.4);
  caption(s, [
    { text: "Each colour is one ID: the software's name for \"the same cell\". ", options: { bold: true } },
    { text: "A moving cell passes a still one. ", options: {} },
    { text: "SORT", options: { bold: true } },
    // SORT numbers its tracks in order of creation, so the lower ID ended and the higher one started
    { text: ` gives the still cell a new ID after the touch (${demo.sort.broke[0].replace("t", "")} becomes ${demo.sort.broke[1].replace("t", "")}). `, options: {} },
    { text: "JPDAF", options: { bold: true } },
    { text: ` keeps both IDs (${ids(demo, "jpdaf")}).` },
  ], 6.35, 0.9);
  s.addNotes(
    "Here is one collision from the video, zoomed in, with the same frames on both sides. " +
    "Each colour is one ID. An ID is the name the software gives a cell so it can say 'this is still the same cell' from one frame to the next. " +
    "A moving cell comes in and passes a still cell. " +
    "On the left, SORT: after the touch, the still cell gets a new ID, so the software thinks it is a new cell. Its path is cut in two. " +
    "On the right, JPDAF: both cells keep their IDs all the way through. " +
    "Both trackers ran on the hand-marked boxes, so the only difference here is the tracking itself."
  );
}

/* 8. Q2: it can go the other way --------------------------------------------- */
{
  const s = pres.addSlide();
  header(pres, s, "QUESTION 2  ·  THE OTHER WAY ROUND", "Here JPDAF swaps the two IDs");
  fnPill(pres, s, "casa.tracking.jpdaf()");
  framed(pres, s, R("13b_swap_sort_vs_jpdaf.gif"), (W - 8.0) / 2, 1.8, 8.0, 4.4);
  caption(s, [
    { text: "JPDAF", options: { bold: true } },
    { text: ` (right): the still cell's ID ${swap.jpdaf.ids[0].replace("t", "")} leaves with the moving cell; ID ${swap.jpdaf.ids[1].replace("t", "")} stays behind. The two cells are mixed up. `, options: {} },
    { text: "SORT", options: { bold: true } },
    { text: " (left) keeps the moving cell's ID but never held the still cell at all." },
  ], 6.35, 0.9);
  s.addNotes(
    "To be fair, JPDAF is not perfect either. In this collision the two IDs swap: " +
    "the ID that belonged to the still cell leaves with the moving cell, and the moving cell's ID stays on the still one. " +
    "The paths look continuous, but they now belong to the wrong cells. " +
    "SORT kept the moving cell's ID here, but it had never tracked the still cell in the first place. " +
    "Swaps like this cannot be counted automatically; you only see them by looking."
  );
}

/* 9. Q2: every collision in the video ----------------------------------------- */
{
  const s = pres.addSlide();
  header(pres, s, "QUESTION 2  ·  ALL THE COLLISIONS", `Every time two cells touched: ${sortKept.n} collisions in 30 seconds`);
  const cw = 4.2, gap = 1.1, x0 = (W - 2 * cw - gap) / 2;
  [
    { num: `${pct(sortKept)}%`, lbl: "SORT", sub: `kept both tracks in ${sortKept.kept} of ${sortKept.n}`, color: INK },
    { num: `${pct(jpdafKept)}%`, lbl: "JPDAF", sub: `kept both tracks in ${jpdafKept.kept} of ${jpdafKept.n}`, color: ORANGE },
  ].forEach((c, i) => {
    const x = x0 + i * (cw + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: 1.95, w: cw, h: 2.6, fill: { color: PANEL }, line: { color: PANEL }, rectRadius: 0.14,
    });
    s.addText(c.lbl, {
      x, y: 2.1, w: cw, h: 0.45, fontFace: FONT, fontSize: 18, bold: true, color: TEXT, align: "center", margin: 0, isTextBox: true,
    });
    s.addText(c.num, {
      x, y: 2.5, w: cw, h: 1.3, fontFace: FONT, fontSize: 72, bold: true, color: c.color, align: "center", margin: 0, isTextBox: true,
    });
    s.addText(c.sub, {
      x, y: 3.85, w: cw, h: 0.45, fontFace: FONT, fontSize: 16, color: MUTED, align: "center", margin: 0, isTextBox: true,
    });
  });
  s.addText("vs", {
    x: x0 + cw, y: 2.95, w: gap, h: 0.7, fontFace: FONT, fontSize: 26, bold: true, color: MUTED,
    align: "center", margin: 0, isTextBox: true,
  });
  s.addText([
    { text: "How we counted", options: { bold: true, color: ORANGE, breakLine: true } },
    { text: `A touch = two hand-marked boxes closer than ${COL.close_px} pixels (a box is about 40). `, options: { breakLine: true } },
    { text: "Kept = the two tracks that met there continue after it.  Lost = one of them ends at the touch, or a new one starts there.", options: { breakLine: true } },
    { text: "Swaps, like the one on the previous slide, cannot be counted this way; that needs hand-labelled identities.", options: { color: MUTED } },
  ], {
    x: x0, y: 4.85, w: 2 * cw + gap, h: 1.9, fontFace: FONT, fontSize: 15, color: TEXT,
    margin: 0, valign: "top", paraSpaceAfter: 4, isTextBox: true,
  });
  s.addNotes(
    `We also counted. Over the whole video, two hand-marked cells came within fourteen pixels of each other ${sortKept.n} times. ` +
    `SORT kept both tracks through ${sortKept.kept} of those touches, ${pct(sortKept)} percent. JPDAF kept both through ${jpdafKept.kept}, ${pct(jpdafKept)} percent. ` +
    "So most touches are fine with either tracker, and JPDAF loses fewer. " +
    "What this count cannot see is a swap, where both tracks continue but on the wrong cells. Counting those would need someone to label which cell is which by hand."
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
    `YOLO26 finds almost every cell (${Math.round(STEP8.yolo26.detection.recall)} of 100) but draws many extra boxes. YOLOv5 misses one cell in four but draws fewer wrong boxes.`,
    `When two cells touch, JPDAF keeps both tracks more often than SORT (${pct(jpdafKept)}% vs ${pct(sortKept)}% of ${sortKept.n} touches).`,
    "Neither tracker is perfect: SORT cuts a path in two, JPDAF can swap two cells. Swaps need a person to spot them.",
  ];
  points.forEach((t, i) => {
    const y = 2.0 + i * 1.45;
    s.addText(String(i + 1), {
      shape: pres.shapes.OVAL, x: M, y, w: 0.7, h: 0.7, fill: { color: ORANGE }, line: { color: ORANGE },
      fontFace: FONT, fontSize: 22, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0, isTextBox: true,
    });
    s.addText(t, {
      x: M + 1.0, y: y - 0.12, w: 6.9, h: 1.1, fontFace: FONT, fontSize: 19, color: WHITE,
      margin: 0, valign: "middle", isTextBox: true,
    });
  });
  framed(pres, s, R("13c_break_strip.png"), 8.75, 1.7, 3.98, 3.6);
  s.addText("SORT (top) and JPDAF (bottom) on the same cell", {
    x: 8.75, y: 4.75, w: 3.98, h: 0.5, fontFace: FONT, fontSize: 13, color: "8A99AD",
    align: "center", margin: 0, valign: "top", isTextBox: true,
  });
  s.addNotes(
    "To sum up. YOLO26 misses almost no cells but draws many false boxes; YOLOv5 is the opposite. For counting cells, YOLO26 is the safer choice. " +
    "When two cells touch, JPDAF keeps both tracks more often than SORT. " +
    "But neither is perfect: SORT tends to cut a path in two, and JPDAF can swap two cells, which only a person can spot. Thank you."
  );
}

/* slide numbers ----------------------------------------------------------------- */
pres.slides.forEach((sl, i) => {
  const dark = i === 0 || i === pres.slides.length - 1;
  sl.addText(String(i + 1), {
    x: W - M - 0.6, y: 7.05, w: 0.6, h: 0.3, fontFace: FONT, fontSize: 11, color: dark ? "8A99AD" : MUTED,
    align: "right", margin: 0, isTextBox: true,
  });
});

pres.writeFile({ fileName: OUT }).then((f) => {
  const mb = fs.statSync(f).size / 1e6;
  console.log(`written: ${f}  (${mb.toFixed(1)} MB, ${pres.slides.length} slides)`);
});
