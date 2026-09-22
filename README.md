# pycasa — hands-on evaluation

Testing [pycasa](https://github.com/DFL-KamLab/pycasa) on its own bundled HC004 session,
for Dr. Moshe Kam's research group. Two layers: the six assigned steps, and a full
public-API sweep that went beyond them.

**Start here:** [FINDINGS.md](FINDINGS.md) — the 140-case coverage table and the complete
evidence chain for the main defect. Every number in it is generated from `outputs/*.json`.

The formal write-up is [`pycasa_Testing_Report.docx`](pycasa_Testing_Report.docx).

---

## What we found

**YOLO26 silently switches its own NMS algorithm.** `ultralytics/utils/nms.py:152` picks
between `torchvision.ops.nms` and its own `TorchNMS` based on whether `torchvision` happens
to be in `sys.modules`. The docstring claims the two match exactly; on this data they
disagree on a few percent of low-confidence boxes. Running YOLOv5 first imports torchvision
and flips the switch, so the same model on the same data spans 77% to 85% F1 depending on
import history. True positives never move — only the false-positive tail does.

Fix: `import torchvision` before YOLO26 inference. One line. Full elimination chain in
[FINDINGS.md](FINDINGS.md).

**JPDAF beats SORT, but only on a long clip.** On the default 101-frame window the gap looks
like noise, +12% track length. On the full 899-frame clip JPDAF holds each cell 93% longer
and needs 35% fewer tracks. Any tracker comparison on three seconds of video understates
the difference.

**Clip length changes the CASA verdict.** YOLO26+SORT's concentration error drops from 24%
to 7% on the full clip, while ground truth with SORT moves the other way, from 14% to 21%
low. The ground-truth gap does not close with more data, which is an open question rather
than a bug: these are the dataset's own annotations, so the detector cannot be blamed.

**The library itself is sound.** 134 of 140 API cases passed. All six binarization methods,
six normalization methods, four moving-cells variants, three trackers, every documented CASA
threshold variant and all five visualization functions work. Error handling is clear in
almost every case.

---

## Setup

```bash
pip install git+https://github.com/DFL-KamLab/pycasa.git
pip install scikit-image scipy motmetrics huggingface_hub torch torchvision \
            ultralytics matplotlib pandas pillow psutil PyYAML requests imageio
pip install git+https://github.com/DFL-KamLab/sort.git
git clone --depth 1 https://github.com/ultralytics/yolov5.git %USERPROFILE%\.pycasa\yolov5
```

Three obstacles are worth knowing about, because each one stops a new user:

| Obstacle | Cause | Resolution |
|---|---|---|
| `No module named 'skimage'` / `scipy` / `torch` | Only numpy, opencv and tqdm are hard requirements | Install the extras explicitly |
| `No module named 'sort'` | The SORT tracker is a separate Git package, not in any extra | Install from `DFL-KamLab/sort` |
| `EOFError` on the first YOLOv5 run | pycasa asks interactively whether to clone the yolov5 repo; with no stdin the `input()` call raises | Pre-clone the repo |

Then, once per shell session:

```bash
call setup_env.bat
```

This sets `PYCASA_DATA` (the HC004 dataset, inside the project folder) and
`PYCASA_PROJECT_ROOT` (the YOLO weights). PowerShell users: `. .\setup_env.ps1`.

Note that `ipython` is not on PATH under a Microsoft Store Python install; use
`python -m IPython` instead.

---

## Reproducing the results

Each script writes its results to `outputs/` as JSON, and the documents are generated
from those files rather than typed by hand.

| Script | What it does |
|---|---|
| `step1_load.py` | Load the default HC004 session, print calibration metadata |
| `step2_timelapse_gt.py` | Ground-truth overlay in the interactive viewer |
| `step3_detection_assessment.py` | YOLOv5, YOLO26 and moving-cells, each scored against ground truth |
| `step5_tracking_gt.py` | SORT and JPDAF on ground truth, rendered to GIF |
| `step6_motility.py` | Kinematic and CASA parameters, compared against the HSTLI report |
| `step7_full_api_test.py` | All 140 API cases, each module group in its own process |
| `step8_full_clip.py` | Steps 3, 5 and 6 repeated on the full 899-frame clip |
| `step9_thread_control.py` | 2x2 controlled experiment: import vs. OpenCV thread count |
| `step9b` – `step9f` | The remaining elimination steps and the two-stage import bisection |

Two scripts carry workarounds for memory rather than analysis. pycasa holds the video as
one contiguous array, so the full clip needs a single 3.3 GB allocation. `step8_full_clip.py`
falls back to shorter windows when that fails, and `make_tracker_sidebyside.py` routes the
load through a disk-backed memory map so the full clip always fits.

Figures and animations for the report and slides are built by `make_report_gifs.py`,
`make_report_figs.py` and `make_tracker_sidebyside.py`, and land in `outputs/report/`.
`build_report.js` assembles the Word document; `build_findings_en.py` assembles
[FINDINGS.md](FINDINGS.md).

---

## Repository layout

```
FINDINGS.md                  evidence page — start here
pycasa_Testing_Report.docx   formal report
scripts/                     everything is reproducible from here
outputs/                     raw results as JSON
outputs/report/              figures and animations used in the report and slides
setup_env.bat / .ps1         per-session environment variables
```

Environment versions behind every number in this repository are recorded in
[`outputs/versions.txt`](outputs/versions.txt).
