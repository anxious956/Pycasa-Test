# pycasa — Test Evidence

Raw results behind the report and the slides. Every number here is read straight
from the JSON files in `outputs/`, which are written by the scripts in `scripts/`.
Nothing is typed by hand.

Environment: see [`outputs/versions.txt`](outputs/versions.txt). Key versions are
`ultralytics==8.3.197`, `torch==2.5.1+cu121`, `opencv-contrib-python==4.14.0.94`,
Python 3.12.10 on Windows 11, RTX 3050 Ti.

## A. Full public-API coverage — 140 cases

Every public function in pycasa called at least once, with its important parameter
variants and with deliberately invalid inputs to check error handling. Each module
group runs in its own Python process, both to bound memory and to isolate the
import contamination described in part B.

```
python scripts/step7_full_api_test.py
```

| Module group | Cases | Passed | What was covered |
|---|---|---|---|
| io | 14 | 13 | load_default_data / load_video, frame ranges, calibration overrides, missing files |
| casa | 23 | 23 | every getter and setter, copy, info, invalid calibration values |
| preprocessing | 19 | 19 | grayscale, 6 binarization methods, 6 normalization methods, chaining |
| detection yolo26 | 8 | 8 | default and custom weights, four confidence thresholds, invalid inputs |
| detection classic | 14 | 13 | 4 moving-cells methods, digital washing, urbano, assessment thresholds |
| detection yolov5 | 3 | 3 | YOLOv5 weights, confidence variants, the ordering test |
| tracking | 19 | 18 | SORT, JPDAF, DeepSORT variants, multi-source, overwrite, MOTA/IDF1 |
| motility | 18 | 15 | kinematic and CASA parameters, all threshold and window variants |
| visualization | 22 | 22 | plot_frame, timelapse, radar, density scatter, interactive calculator |
| **total** | **140** | **134** |  |

A pass on a deliberately invalid input means the function raised the appropriate
error. 134 of 140 passed. The 6 failures are the defects below, not test artefacts.

### The failures

- `session.io.load_default_data()` is missing `volume_ml` and `chamber_depth_um`
  - The module-level function accepts them; the session wrapper raises TypeError.
- `evaluate_detections()` with no detector run
  - Warns and writes an all-zero result rather than raising. Defensible, but a zero score reads like a bad detector.
- `evaluate_tracks()` with no tracking run
  - Skips with `skipped=True` and a reason instead of raising. This one is good behaviour; the test expectation was wrong.
- `overlap` is not validated
  - 1.5, 5.0 and -0.5 are all accepted silently. Passing 50 as a percentage multiplies the work about thirtyfold.
- `kinematic_parameters()` with no tracking run
  - Returns an empty result with no error and no warning.
- `kinematic_parameters()` when `um_per_px` is None
  - The load-time warning says motility "will not compute"; the call then raises ValueError. Inconsistent messaging.

Three of these six are genuine defects (numbers 1, 4 and 5 in that order); the
others describe behaviour that is defensible but surprising. See the report for the
prioritised list.

Full per-case table: [`outputs/step7_api_test_report.md`](outputs/step7_api_test_report.md)

## B. YOLO26 changes its own NMS algorithm depending on what is imported

### B.1 Symptom

YOLO26 gives different results on identical data with identical weights, depending
only on what ran earlier in the same Python process. True positives stay fixed;
only the false-positive tail moves.

| Run | Frames | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| isolated process | 101 | 9,985 | 5,806 | 107 | 63.23% | 98.94% | 77.15% |
| after YOLOv5, same process | 101 | 9,985 | 4,797 | 107 | 67.55% | 98.94% | 80.28% |
| isolated process | 899 (full clip) | 80,271 | 42,369 | 808 | 65.45% | 99.00% | 78.81% |

Recall is pinned because TP and FN do not move. Precision carries the whole change,
and F1 follows it.

### B.2 Thread count ruled out (controlled 2x2)

The obvious candidate was OpenCV's thread count, which the YOLOv5 import drops from
the default to one. Tested directly rather than inferred: the import and the thread
count were varied independently, each condition in its own process.

| Run | YOLOv5 imported | cv2 threads | Detections | TP | FP | F1 |
|---|---|---|---|---|---|---|
| A | no | 16 | 6,390 | 4,120 | 2,270 | 78.00% |
| B | no | 1 | 6,390 | 4,120 | 2,270 | 78.00% |
| C | yes | 1 | 6,003 | 4,120 | 1,883 | 80.97% |
| D | yes | 16 | 6,003 | 4,120 | 1,883 | 80.97% |

A equals B and C equals D, so the thread count changes nothing on its own. B against D
differs by 387 detections with the thread count held equal, so the import does.
True positives are 4,120 in all four conditions.

Script: `scripts/step9_thread_control.py`

### B.3 Four more candidates ruled out

| Candidate | Test | Detections | Verdict |
|---|---|---|---|
| Module shadowing | import YOLOv5, then delete `models` / `utils` from `sys.modules` | 6,003 (vs 6,390 isolated) | not the cause |
| Environment variables | set all five the import writes, before torch, with no YOLOv5 import | 6,390 (vs 6,390 isolated) | not the cause |
| `import ultralytics` | import the shared package alone | 6,390 (vs 6,390 isolated) | not the cause |
| `ultralytics.utils.patches` | import the patching module alone | 6,390 (vs 6,390 isolated) | not the cause |

Torch global flags (thread counts, cuDNN benchmark and determinism, TF32 on both
paths, float32 matmul precision, default dtype, gradient mode) were byte-identical
before and after the import. `torchvision.ops.nms` is the same function object, so it
had not been monkey-patched. Passing `conf` explicitly still shifts the result.

Scripts: `scripts/step9b_module_shadow.py`, `step9c_env_test.py`, `step9d_ultralytics_test.py`

### B.4 Bisecting the import chain

Each module that `models/common.py` imports, run alone in its own process:

| Imported | Detections | FP | F1 | Verdict |
|---|---|---|---|---|
| (nothing imported) | 6,390 | 2,270 | 78.00% | reference |
| ultralytics.utils.plotting | 6,390 | 2,270 | 78.00% | no effect |
| utils (yolov5 package init) | 6,390 | 2,270 | 78.00% | no effect |
| utils.dataloaders | 6,003 | 1,883 | 80.97% | **reproduces it** |
| utils.general | 6,003 | 1,883 | 80.97% | **reproduces it** |
| utils.torch_utils | 6,003 | 1,883 | 80.97% | **reproduces it** |
| models.common (the full import) | 6,003 | 1,883 | 80.97% | reference |

`utils.dataloaders` and `utils.torch_utils` both import `utils.general`, so the
common factor is `utils.general`. Bisecting inside that file:

| Imported | Detections | FP | Verdict |
|---|---|---|---|
| (nothing imported) | 6,390 | 2,270 | reference |
| **`import torchvision`** | 6,003 | 1,883 | **reproduces it** |
| yaml, packaging | 6,390 | 2,270 | no effect |
| ultralytics.data.converter | 6,390 | 2,270 | no effect |
| ultralytics.utils.checks | 6,390 | 2,270 | no effect |
| ultralytics.utils.files | 6,390 | 2,270 | no effect |
| ultralytics.utils.git | 6,390 | 2,270 | no effect |
| ultralytics.utils.ops | 6,390 | 2,270 | no effect |
| ultralytics.utils.torch_utils | 6,390 | 2,270 | no effect |
| ultralytics.utils.patches | 6,390 | 2,270 | no effect |
| utils.downloads | 6,390 | 2,270 | no effect |
| utils.metrics | 6,390 | 2,270 | no effect |
| the module-level settings block (lines 79-87) | 6,390 | 2,270 | no effect |
| utils.general (the whole file) | 6,003 | 1,883 | reference |

One line out of the whole chain reproduces the shift: `import torchvision`.

Scripts: `scripts/step9e_bisect.py`, `scripts/step9f_bisect_general.py`

### B.5 Root cause

`ultralytics/utils/nms.py`, lines 151-157, picks the NMS implementation at call time
based on whether `torchvision` happens to be loaded:

```python
if "torchvision" in sys.modules:
    i = torchvision.ops.nms(boxes, scores, iou_thres)   # compiled reference kernel
else:
    i = TorchNMS.nms(boxes, scores, iou_thres)          # ultralytics' own pure-PyTorch kernel
```

The `TorchNMS` docstring states that it "matches torchvision behavior exactly". On this
data it does not: the two disagree on a few percent of low-confidence, overlapping boxes.

pycasa's YOLOv5 loader imports `torchvision` explicitly before building the model
(`pycasa/detection/_yolo.py`, `_load_standard_yolov5_model`), so running YOLOv5 first
flips the switch for every later YOLO26 call in that process. An isolated pycasa run
never imports torchvision, which was confirmed by inspecting `sys.modules` before and
after inference — so pycasa's default YOLO26 path uses the fallback kernel.

The decisive test: import torchvision, then delete it from `sys.modules` while its
libraries stay loaded in memory.

| Condition | Detections | F1 |
|---|---|---|
| torchvision not imported | 6,390 | 78.00% |
| torchvision imported | 6,003 | 80.97% |
| imported, then removed from `sys.modules` | 6,390 | 78.00% |

Removing the name restores the original result, so the switch is the registry check
itself, not any numerical side effect of loading the package.

### B.6 Fix

For pycasa: `import torchvision` before running YOLO26, so inference always uses the
reference kernel regardless of what else the process has loaded. One line.

For ultralytics: the equivalence claim in the `TorchNMS` docstring does not hold on
this data, and selecting an algorithm from `sys.modules` makes output depend on import
history. Worth reporting upstream.

Until either lands, any published YOLO26 precision or F1 figure should state whether
torchvision was loaded, because the same model on the same data spans several points of F1.

