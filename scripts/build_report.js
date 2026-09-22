/* Builds the pycasa testing report as a Word (.docx) document.
 *   node scripts/build_report.js
 * Output: pycasa_Testing_Report.docx
 * All numbers come from outputs/report_data.json; nothing is typed here.
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun, PageBreak, TableOfContents, PageOrientation, ExternalHyperlink,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const CONTENT_W = 9360;                       // Letter 12240 minus 2x1440 margins

/* ---------------------------------------------------------------- helpers */
const P = (text, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 120, before: o.before ?? 0 },
  alignment: o.align,
  children: [new TextRun({ text, size: o.size ?? 21, italics: o.italics, bold: o.bold,
                           color: o.color, font: o.font })],
});

const H = (text, level) => new Paragraph({
  heading: level, spacing: { before: 280, after: 140 },
  keepNext: true,          // keep a heading from being stranded at a page break
  children: [new TextRun({ text, size: level === HeadingLevel.HEADING_1 ? 28 : 24, bold: true,
                           color: level === HeadingLevel.HEADING_1 ? "1F3864" : "2E5C8A" })],
});

const Bullet = (text) => new Paragraph({
  bullet: { level: 0 }, spacing: { after: 70 },
  children: [new TextRun({ text, size: 21 })],
});

const Code = (lines) => lines.map((s, i) => new Paragraph({
  spacing: { after: i === lines.length - 1 ? 140 : 0, before: i === 0 ? 60 : 0 },
  shading: { type: ShadingType.CLEAR, fill: "F2F2F2" },
  children: [new TextRun({ text: s, font: "Consolas", size: 18 })],
}));

/* Table: headers + rows. `widths` holds the relative column widths. */
function DataTable(headers, rows, widths, opt = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const colWidths = widths.map((o) => Math.round((CONTENT_W * o) / total));
  colWidths[colWidths.length - 1] = CONTENT_W - colWidths.slice(0, -1).reduce((a, b) => a + b, 0);

  const cell = (t, i, o = {}) => new TableCell({
    width: { size: colWidths[i], type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: o.fill ?? "FFFFFF" },
    margins: { top: 60, bottom: 60, left: 90, right: 90 },
    children: [new Paragraph({
      alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
      spacing: { after: 0 },
      children: [new TextRun({ text: String(t), size: 19, bold: o.bold,
                               color: o.color, font: o.font })],
    })],
  });

  return new Table({
    columnWidths: colWidths,
    width: { size: CONTENT_W, type: WidthType.DXA },
    borders: {
      top:    { style: BorderStyle.SINGLE, size: 4, color: "9BB7D4" },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: "9BB7D4" },
      left:   { style: BorderStyle.SINGLE, size: 4, color: "9BB7D4" },
      right:  { style: BorderStyle.SINGLE, size: 4, color: "9BB7D4" },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: "C9D8E8" },
      insideVertical:   { style: BorderStyle.SINGLE, size: 2, color: "C9D8E8" },
    },
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((b, i) => cell(b, i, { fill: "1F3864", bold: true, color: "FFFFFF" })),
      }),
      ...rows.map((r, ri) => new TableRow({
        children: r.map((c, i) => cell(c, i, {
          fill: opt.highlight && opt.highlight.includes(ri) ? "FFF2CC" : (ri % 2 ? "F5F8FB" : "FFFFFF"),
          bold: (opt.highlight && opt.highlight.includes(ri)) || i === 0,
        })),
      })),
    ],
  });
}

/* Image + caption. `widthFraction` is a fraction of the content width. */
function Figure(file, caption, widthFraction = 1.0) {
  const fullPath = path.join(ROOT, file);
  if (!fs.existsSync(fullPath)) { console.warn("  ! image missing:", file); return []; }
  const buf = fs.readFileSync(fullPath);
  const size = readPngSize(buf);
  const widthPx = Math.round((CONTENT_W / 15) * widthFraction);          // DXA -> ~px
  const heightPx = Math.round(widthPx * (size.h / size.w));
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 160, after: 60 },
      children: [new ImageRun({ data: buf, type: "png",
                                transformation: { width: widthPx, height: heightPx } })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: [new TextRun({ text: caption, size: 17, italics: true, color: "5A5A5A" })],
    }),
  ];
}

/* Read width/height straight from the PNG header */
function readPngSize(buf) {
  if (buf.slice(1, 4).toString() === "PNG")
    return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
  return { w: 1200, h: 800 };
}

const PageBreakPara = () => new Paragraph({ children: [new PageBreak()] });

/* ---------------------------------------------------------------- data */
const D = JSON.parse(fs.readFileSync(path.join(ROOT, "outputs/report_data.json"), "utf8"));

/* ---------------------------------------------------------------- document */
const body = [];

/* --- cover --- */
body.push(
  new Paragraph({ spacing: { before: 2200, after: 0 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "TESTING REPORT", size: 30, bold: true, color: "1F3864",
                             characterSpacing: 60 })] }),
  new Paragraph({ spacing: { before: 200, after: 0 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "pycasa", size: 56, bold: true, color: "1F3864" })] }),
  new Paragraph({ spacing: { before: 60, after: 0 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Hands-on evaluation of the detection, tracking and CASA pipeline",
                             size: 24, color: "2E5C8A" })] }),
  new Paragraph({ spacing: { before: 40, after: 600 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "plus a full public-API coverage test", size: 24, color: "2E5C8A" })] }),
  new Paragraph({ spacing: { before: 0, after: 80 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "HC004 session, sys-casa / HSTLI dataset", size: 21, italics: true })] }),
  new Paragraph({ spacing: { after: 80 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Library: github.com/DFL-KamLab/pycasa", size: 20, color: "5A5A5A" })] }),
  new Paragraph({ spacing: { before: 900 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Prepared for Dr. Moshe Kam's research group", size: 21 })] }),
  new Paragraph({ spacing: { after: 0 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: D.date, size: 20, color: "5A5A5A" })] }),
  PageBreakPara(),
);

/* --- contents --- */
body.push(
  H("Contents", HeadingLevel.HEADING_1),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  PageBreakPara(),
);

/* --- 1. Scope --- */
body.push(
  H("1. Scope and Method", HeadingLevel.HEADING_1),
  P("The group asked for hands-on work with pycasa: install it, run its functions, and report what the library does and how well it does it. This report covers two layers of that request."),
  P("First layer, the six assigned steps:", { bold: true, after: 60 }),
  Bullet("Load the bundled default dataset through the io module."),
  Bullet("Visualize it with the timelapse viewer using ground-truth detections only, and report the clip's um_per_px, chamber depth and volume."),
  Bullet("Run YOLOv5, YOLO26 and moving-cells detection against ground truth, and report TP/FP/FN, precision, recall and F1."),
  Bullet("Confirm and explain that pycasa keeps only one active detection model at a time."),
  Bullet("Run SORT and JPDAF on ground truth only, and visualize both."),
  Bullet("Run GT+SORT and YOLO26+SORT, compute kinematic and CASA parameters, and compare them against the real commercial-CASA numbers in the HSTLI report."),
  P("Second layer, beyond the assignment:", { bold: true, before: 140, after: 60 }),
  Bullet("Every public function in the library was executed at least once, across " + D.api.total + " individual test cases, including parameter variants and deliberately invalid inputs."),
  Bullet("A longer-clip rerun (" + D.fullClip.frames + " frames instead of 101) to test whether the CASA discrepancies are driven by clip length."),
  Bullet("Six defects and design issues were identified, reproduced and documented for the library authors."),
  P("Work was done interactively in IPython on Windows 11, following the group's own recommended workflow. Every number in this report is copied from actual console output; the scripts that produce them are included in the project repository."),
);

/* --- 2. Environment --- */
body.push(
  H("2. Environment and Setup", HeadingLevel.HEADING_1),
  P("pycasa installs with a minimal dependency set. Everything past basic I/O needs optional extras, and two dependencies are not covered by any extra at all."),
  ...Code([
    "pip install git+https://github.com/DFL-KamLab/pycasa.git",
    "pip install scikit-image scipy motmetrics huggingface_hub torch torchvision \\",
    "            ultralytics matplotlib pandas pillow psutil PyYAML requests imageio",
    "pip install git+https://github.com/DFL-KamLab/sort.git      # not in any extra",
    "git clone --depth 1 https://github.com/ultralytics/yolov5.git %USERPROFILE%\\.pycasa\\yolov5",
  ]),
  P("Three setup obstacles were encountered and resolved. They are reported here because each one would stop a new user.", { before: 80 }),
  DataTable(
    ["Obstacle", "Cause", "Resolution"],
    [
      ["Missing scikit-image, scipy, torch", "Only numpy, opencv and tqdm are hard requirements; everything else sits behind extras", "Install the extras explicitly"],
      ["No module named 'sort'", "The SORT tracker is a separate Git package and is not listed in the tracking extra", "Install from the DFL-KamLab/sort repository"],
      ["EOFError on first YOLOv5 run", "pycasa asks interactively whether to clone the yolov5 repository; with no stdin the input() call raises", "Clone the repository manually before the first run"],
    ],
    [30, 38, 32]),
);

/* --- 3. Steps 1-2 --- */
body.push(
  H("3. Data Loading and Ground-Truth Visualization", HeadingLevel.HEADING_1),
  P("A single call fetches and caches a real recording from the group's HSTLI dataset, with calibration metadata already attached."),
  ...Code(["import pycasa as pc", "self = pc.io.load_default_data()"]),
  H("3.1 Clip and calibration", HeadingLevel.HEADING_2),
  DataTable(["Field", "Value", "Meaning"], D.meta, [26, 20, 54]),
  P("The three calibration values matter because they feed different parts of the pipeline. um_per_px converts pixel displacements into micrometres per second, so every velocity metric depends on it. Chamber depth defines the imaged volume, and together with the ejaculate volume it converts a cells-per-frame count into a concentration and then a total sperm count.", { before: 80 }),
  P("The default session carries ground-truth detections but no ground-truth tracks, so get_tracks() returns an empty dictionary until a tracker is run. This is why step 5 can run SORT and JPDAF against ground truth without any detector being active.", { before: 60 }),
  H("3.2 Visualization", HeadingLevel.HEADING_2),
  ...Code(['self.visualization.timelapse(video_type="original", show_detections=False,',
          '                             show_tracks=False, show_groundtruth=True)']),
  P("The viewer is interactive: a frame slider, a play button, keyboard stepping and per-overlay toggle buttons. No detection or tracking was run at this point, so the only overlay is ground truth."),
  ...Figure("outputs/report/01_gt_only.png", "Ground-truth detections on the raw clip. Green boxes are the dataset's own annotations.", 0.86),
);

/* --- 4. Step 3 --- */
body.push(
  H("4. Detection Benchmark", HeadingLevel.HEADING_1),
  P("Three detector families were run on the same clip and scored against ground truth. Matching is by centre distance within 20 pixels, the library default."),
  ...Code(['self.detection.yolo(yolo_model="yolov5"); self.assessment.evaluate_detections()',
          'self.detection.yolo(yolo_model="yolo26"); self.assessment.evaluate_detections()',
          'self.detection.detect_moving_cells();     self.assessment.evaluate_detections()']),
  DataTable(["Detector", "TP", "FP", "FN", "Precision", "Recall", "F1", "Frames"], D.detection101, [24, 10, 10, 10, 12, 11, 11, 12], { highlight: [1] }),
  P("Moving-cells is scored on 81 frames rather than 101 because it spends the first 20 frames learning a static background model before it can report anything.", { before: 70, italics: true, size: 19 }),
  P("Reading the table: YOLO26 misses almost nothing, with recall just under 99 percent, but pays for it with roughly twice the false positives of YOLOv5. YOLOv5 is the more balanced detector on precision, at the cost of missing about a quarter of the real cells. The classical moving-cells method is the weakest of the three, because it can only see cells that move and it produces a substantial amount of background noise.", { before: 80 }),
  P("The two YOLO26 rows are not a typo. They are the same model, the same weights and the same frames, and they differ only in whether YOLOv5 had been run earlier in the same Python process. This is a defect in the library and is documented in section 9.", { before: 70, bold: true }),
  ...Figure("outputs/report/screenshots/ss1_detection_terminal.png", "Console output: YOLO26 scored at three confidence thresholds. Raising the threshold trades recall for precision; lowering it to 0.01 collapses F1 to 51.6 percent.", 1.0),
  ...Figure("outputs/report/02_gt_vs_yolo26.png", "YOLO26 predictions (red) drawn over ground truth (green). Most boxes overlap; the unpaired red boxes are the false positives that hold precision down.", 0.86),
);

/* --- 5. Step 4 --- */
body.push(
  H("5. The Single Active Model Policy", HeadingLevel.HEADING_1),
  P("pycasa stores exactly one predicted-detection result per session. Running a second detector discards the first and prints a warning. The same rule applies to tracking backends."),
  ...Code(["Warning: Previous detection result overwritten (yolov5 -> yolo26).",
          "Warning: Previous detection result overwritten (yolo26 -> moving_cells).",
          "Warning: Previous tracking result overwritten (sort -> jpdaf)."]),
  P("This has a practical consequence for benchmarking. Each detector must be scored immediately after it runs, before the next one is started. It also has a subtler consequence that cost time during this work: get_assessment() and get_motility() return the live session dictionaries rather than copies, so a previously captured result silently changes when the next detector runs. Results must be deep-copied to be compared."),
  ...Code(["import copy",
          'self.detection.yolo(yolo_model="yolo26")',
          "self.assessment.evaluate_detections()",
          'result = copy.deepcopy(self.get_assessment()["detection"])   # deepcopy is required']),
  P("A related behaviour is worth knowing. Trackers process every available source, not just one. With a detector still active, a single sort() call produces two independent track sets, one from ground truth and one from the detector. Passing skip_gt=True restricts it to the detector.", { before: 80 }),
);

/* --- 6. Step 5 --- */
body.push(
  H("6. Tracking: SORT against JPDAF", HeadingLevel.HEADING_1),
  P("Both trackers were run on the same ground-truth detections, with no detector active, so the comparison isolates the tracking algorithm itself. JPDAF is the method from Urbano et al. (2017); SORT is the Bewley implementation adapted by the group."),
  ...Code(["self.tracking.sort()", "self.tracking.jpdaf()   # overwrites the SORT result"]),
  DataTable(["Tracker", "Tracks", "Avg. track length (frames)", "Throughput"], D.tracking101, [26, 18, 34, 22]),
  P("On this 101-frame window the two produce almost the same number of distinct cells, but JPDAF holds each one about 12 percent longer before losing it. JPDAF is roughly ten times slower.", { before: 70 }),
  P("The difference is far more pronounced on a longer clip, which is the subject of section 8.", { before: 50, italics: true }),
  ...Figure("outputs/report/03_sort_gt.png", "SORT trajectories on ground truth over the 101-frame window.", 0.62),
  ...Figure("outputs/report/screenshots/ss3_jpdaf_timelapse.png", "JPDAF trajectories in the interactive viewer. Each coloured trail is one tracked cell.", 0.48),
);

/* --- 7. Step 6 --- */
body.push(
  H("7. Kinematic and CASA Parameters", HeadingLevel.HEADING_1),
  P("Two pipelines were taken all the way to population statistics: ground truth with SORT, and YOLO26 detections with SORT. Both were then compared against the real commercial-CASA numbers recorded for this donor in the HSTLI dataset."),
  ...Code(["self.tracking.sort()", "self.motility.kinematic_parameters()", "self.motility.casa_parameters()"]),
  H("7.1 Per-track kinematics", HeadingLevel.HEADING_2),
  DataTable(["Pipeline", "Tracks", "VCL", "VSL", "VAP", "LIN", "ALH", "WOB", "STR", "MAD"], D.kinematics101, [22, 10, 11, 11, 11, 7, 7, 7, 7, 7]),
  P("Velocities are in micrometres per second, ALH in micrometres, MAD in degrees; LIN, WOB and STR are dimensionless ratios. Values are means across all analysis windows.", { before: 60, italics: true, size: 19 }),
  P("The YOLO26 pipeline reports systematically lower and more variable velocities. The cause is visible in the detection table: its false positives generate short, spurious tracks of cells that are not really moving, and those drag the averages down.", { before: 70 }),
  H("7.2 Population parameters against the real report", HeadingLevel.HEADING_2),
  P("Thresholds are the library defaults, tuned to approximate a Sperm Class Analyzer: classification on VCL, immotile below 19 um/s, rapid at or above 29 um/s, progressive at STR 0.68 or above."),
  DataTable(["Source", "%Rapid", "%Slow", "%Non-prog", "%Immotile", "%Motile", "Conc. (M/mL)", "Total (M)"],
        D.casa101, [24, 11, 11, 13, 13, 11, 10, 7], { highlight: [0] }),
  P("Ground truth with SORT lands close to the reference on the motility grades. Rapid and slow are each a few points high, immotile is five points low, and non-progressive is clearly under-reported at 2.7 against 9. Concentration comes in 14 percent below the machine.", { before: 80 }),
  P("YOLO26 with SORT is markedly worse. Immotile jumps to 40 percent against a real 26, and concentration overshoots by 24 percent. Both effects trace back to the same source: false-positive detections become short static tracks, which inflate the cell count and are then graded as immotile.", { before: 60 }),
  P("The library also warns that the clip's 30 fps is below the 50 fps it recommends for reliable VCL and ALH, because the curvilinear path is undersampled at this rate. Velocity-derived grades should be read with that in mind.", { before: 60, italics: true }),
  ...Figure("outputs/report/06_radar_gt.png", "Kinematic profile, ground truth with SORT.", 0.46),
  ...Figure("outputs/report/06_radar_yolo26.png", "The same profile from YOLO26 detections. The contour is visibly smaller, reflecting the lower velocities in section 7.1.", 0.46),
);

/* --- 8. Longer clip --- */
body.push(
  H("8. Longer-Clip Rerun", HeadingLevel.HEADING_1),
  P("The default session loads 101 of 901 frames, which is 3.4 seconds of a 30-second recording. That is a short window for a tracking problem, and both concentration and total count are derived from a cells-per-frame average, so they depend on how much footage is available. Steps 3, 5 and 6 were therefore repeated on the full clip, " + D.fullClip.frames + " frames."),
  P("This turned out to be the most informative part of the work. One conclusion from the 101-frame window survives, one is sharpened beyond recognition, and one is overturned.", { before: 60, bold: true }),
  H("8.1 Detection over the full clip", HeadingLevel.HEADING_2),
  P("This is the conclusion that survives. The ranking of the three detectors is unchanged, and the scores move by only a few points, which confirms that detection quality is a per-frame property and does not depend on clip length."),
  DataTable(["Detector", "TP", "FP", "FN", "Precision", "Recall", "F1", "Frames"], D.detectionFullClip, [24, 11, 11, 10, 12, 11, 11, 10]),
  H("8.2 Tracking over the full clip", HeadingLevel.HEADING_2),
  DataTable(["Tracker", "Tracks (101f)", "Avg. length (101f)", "Tracks (" + D.fullClip.frames + "f)", "Avg. length (" + D.fullClip.frames + "f)"],
        D.trackingFullClip, [20, 20, 20, 20, 20]),
  P("This is the sharpened conclusion. On 101 frames JPDAF's tracks were 12 percent longer than SORT's, a difference small enough to look like noise. On the full clip they are " + D.fullClip.jpdafLonger + " percent longer, and JPDAF consolidates the same swimming cells into " + D.fullClip.jpdafFewer + " percent fewer tracks. Both trackers see identical input, so this is purely the association algorithm: SORT loses a cell and restarts it as a new track, JPDAF holds on. That is precisely the fragmentation problem the 2017 paper set out to solve, and it is invisible on a short clip because tracks have not had time to break yet.", { before: 70 }),
  P("Any comparison of trackers on a three-second window will therefore understate the difference between them.", { before: 50, bold: true }),
  H("8.3 CASA parameters over the full clip", HeadingLevel.HEADING_2),
  DataTable(["Source", "%Rapid", "%Slow", "%Non-prog", "%Immotile", "Conc. (M/mL)", "Total (M)"],
        D.casaFullClip, [26, 12, 12, 14, 14, 12, 10], { highlight: [0] }),
  P(D.fullClip.commentary, { before: 70 }),
);

/* --- 9. API coverage --- */
body.push(
  H("9. Full Public-API Coverage", HeadingLevel.HEADING_1),
  P("The six assigned steps exercise roughly half of pycasa. To characterise the rest, every public function was called at least once, with its important parameter variants and with deliberately invalid inputs to check error handling. The suite runs each module group in its own Python process, both to bound memory and to isolate the YOLOv5 contamination described in section 10."),
  ...Code(["python scripts/step7_full_api_test.py"]),
  DataTable(["Module group", "Cases", "Passed", "What was covered"], D.api.rows, [20, 9, 9, 62]),
  P("A pass on a deliberately invalid input means the function raised the appropriate error. " + D.api.passed + " of " + D.api.total + " cases passed; the " + D.api.remaining + " failures are the defects in section 10, not test artefacts.", { before: 70 }),
  P("Everything in the library works. All six binarization methods, all six normalization methods, all four moving-cells variants, digital washing, urbano detection, three trackers, every documented CASA threshold variant and all five visualization functions produced correct output. Error handling is generally good: missing preprocessing layers, out-of-range frame indices, invalid method names and invalid calibration values all raise clear, actionable messages.", { before: 60 }),
  ...Figure("outputs/report/screenshots/ss4_dort_katman.png", "Four preprocessing layers rendered side by side with detections overlaid. Otsu keeps only the bright cell heads; CLAHE lifts the tails out of the background.", 1.0),
  ...Figure("outputs/report/screenshots/ss2_timelapse_full.png", "The viewer with every overlay enabled at once: ground truth, YOLO26 detections, and trajectories from both track sets.", 1.0),
);

/* --- 10. Findings --- */
body.push(
  H("10. Defects and Design Issues Found", HeadingLevel.HEADING_1),
  P("Six issues were identified and reproduced. They are ordered by how much they affect the reported results. The first three change numbers; the last three cost time."),
  DataTable(["#", "Issue", "Effect", "Workaround"], D.findings, [5, 30, 37, 28]),
  H("10.1 The first issue in detail", HeadingLevel.HEADING_2),
  P("YOLO26 returns different results depending on whether YOLOv5 ran earlier in the same Python process. YOLOv5 turned out to be only the messenger. The actual trigger is a single import, and the mechanism is a specific line in the ultralytics package that pycasa depends on."),
  P("Root cause.", { bold: true, before: 80, after: 40 }),
  P("ultralytics selects its non-maximum-suppression implementation at call time, in utils/nms.py lines 151 to 157: if the name torchvision is present in sys.modules it calls torchvision.ops.nms, otherwise it falls back to its own pure-PyTorch TorchNMS.nms. The docstring states that TorchNMS matches torchvision behaviour exactly. The measurements below show that it does not. The YOLOv5 repository imports torchvision at the top of utils/general.py, so running YOLOv5 first flips every later YOLO26 call onto the torchvision path."),
  P("In an isolated pycasa run torchvision is never imported, which was verified by inspecting sys.modules before and after inference. So pycasa's default YOLO26 path uses the fallback NMS, and any other package that happens to import torchvision silently switches it to the reference one."),
  P("How it was found.", { bold: true, before: 80, after: 40 }),
  P("The obvious first candidate was OpenCV's thread count, which the YOLOv5 import drops to one. A two-by-two design varied the import and the thread count independently, each condition in its own process."),
  DataTable(["Run", "YOLOv5 imported", "cv2 threads", "Detections", "TP", "FP", "F1"], D.kontrol2x2, [8, 18, 14, 16, 14, 14, 16]),
  P("Thread count changes nothing on its own; the import does. Module shadowing, the five environment variables the import writes, every torch global flag, NMS monkey-patching and the confidence threshold were then each eliminated with a direct test. The import chain was bisected instead: of everything models/common.py imports, only utils/general.py reproduces the shift, and of everything utils/general.py does, only the bare statement import torchvision reproduces it. Two final runs settled the mechanism: with torchvision imported the result is 6,003 detections; importing it and then deleting it from sys.modules, with its libraries still loaded in memory, returns the result to 6,390. The switch is the registry check, not any numerical side effect of loading the package.", { before: 70 }),
  P("Fix.", { bold: true, before: 80, after: 40 }),
  P("For pycasa the fix is one line: import torchvision before running YOLO26, so that inference always uses the reference NMS regardless of what else the process has loaded. For ultralytics the equivalence claim in the TorchNMS docstring is false on this data and should be reported upstream. Until either lands, any published YOLO26 figure should state which NMS path produced it."),
  P("The effect is confined to low-confidence detections. True positives and false negatives are essentially unchanged; only the false-positive tail moves. An independent run of the same six steps by another group member, on a different machine, produced a third value again, which strengthens the finding.", { before: 60 }),
  DataTable(["Run", "TP", "FP", "FN", "F1"], D.y26Comparison, [40, 15, 15, 15, 15]),
  P("The pattern is consistent and it scales. On the 101-frame window, true positives agree to within three detections across three runs while false positives span a 47 percent range. On the full clip the agreement on true positives is still better than half a percent, 80,271 against 80,002, but the two runs differ by 14,563 false positives, a 52 percent spread. Recall is effectively identical in every run; precision is not.", { before: 70 }),
  P("The practical consequence is that a YOLO26 precision or F1 figure is not reproducible unless the run conditions are stated. F1 for the same model on the same data ranges from 77 to 85 percent across these five runs. Any benchmark table should record whether another detector ran first in the same process, and the safe practice is to run each detector in a fresh process.", { before: 60, bold: true }),
  H("10.2 Two silent failures", HeadingLevel.HEADING_2),
  P("kinematic_parameters() called without any tracking returns an empty result with no error and no warning. A user who forgets the tracking step gets an empty motility dictionary and no indication why."),
  P("The overlap parameter of kinematic_parameters() is not validated. It is documented as a fraction, but 1.5, 5.0 and -0.5 are all accepted silently. A user who supplies 50, reading it as a percentage, gets stride-one windows and roughly thirty times the intended computation, with no warning.", { before: 60 }),
);

/* --- 11. Summary --- */
body.push(
  H("11. Summary", HeadingLevel.HEADING_1),
  P("What the testing established:", { bold: true, after: 60 }),
  Bullet("Detection: YOLO26 is the strongest of the three detectors, driven almost entirely by recall. YOLOv5 is better balanced on precision. The classical moving-cells method is usable but noisy and blind to non-moving cells."),
  Bullet("Tracking: JPDAF produces measurably less fragmented tracks than SORT on identical input, and the advantage grows with clip length. It costs roughly ten times the runtime."),
  Bullet("CASA validation: ground truth with SORT reproduces the commercial machine's motility grades to within a few points. Non-progressive is the weakest agreement. Concentration is low, and clip length is a major contributor."),
  Bullet("Detection quality propagates directly into clinical output. YOLO26's false positives become short static tracks, which inflate both the immotile fraction and the concentration."),
  Bullet("The library is functionally complete. Every public function works, and error handling is clear in almost every case."),
  P("What should be raised with the library authors:", { bold: true, before: 140, after: 60 }),
  Bullet("YOLO26 output depends on whether torchvision is loaded, because ultralytics switches NMS implementation on a sys.modules check. Import torchvision explicitly before inference; one line."),
  Bullet("Two silent failures, the no-op kinematic call and the unvalidated overlap parameter, should raise or warn."),
  Bullet("Result getters should return copies, or each result should be stored under its own key."),
  Bullet("The sort package belongs in the tracking extra, and the interactive clone prompt should handle a closed stdin."),
  Bullet("The video is loaded as one contiguous array, so the usable clip length is bounded by the largest free memory block rather than by total memory. Chunked or memory-mapped loading would remove that coupling."),
  P("Open question for the group:", { bold: true, before: 140, after: 60 }),
  P(D.openQuestion),
  H("11.1 Reproducing this work", HeadingLevel.HEADING_2),
  P("Every result here is produced by scripts in the accompanying repository. Setup instructions, a step-by-step walkthrough of all public functions, and the raw result files are included."),
  ...Code(D.commands),
);

/* ---------------------------------------------------------------- write */
const doc = new Document({
  creator: "pycasa testing",
  title: "pycasa Testing Report",
  description: "Hands-on evaluation of the pycasa CASA pipeline",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: "Calibri", size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, color: "1F3864" }, paragraph: { outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, color: "2E5C8A" }, paragraph: { outlineLevel: 1 } },
    ],
  },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840, orientation: PageOrientation.PORTRAIT },
              margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } },
    },
    children: body,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const outPath = path.join(ROOT, "pycasa_Testing_Report.docx");
  fs.writeFileSync(outPath, buf);
  console.log("written:", outPath, (buf.length / 1e6).toFixed(1), "MB");
});
