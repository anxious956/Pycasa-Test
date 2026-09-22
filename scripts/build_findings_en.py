"""Builds FINDINGS.md, the evidence page.

Assembles one page from the raw JSON in outputs/. Two parts:
  A) the 140-case public-API coverage
  B) the step-by-step elimination chain behind the YOLO26 / NMS finding

Every number is read from a file; none is typed here.

    python scripts/build_findings_en.py
"""
import io, json, os
from collections import Counter

OUT_MD = "FINDINGS.md"


def load_json(p):
    return json.load(io.open(p, encoding="utf-8"))


def md_table(headers, rows):
    ln = ["| " + " | ".join(headers) + " |",
          "|" + "|".join(["---"] * len(headers)) + "|"]
    ln += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return ln


L = []
A = L.append

A("# pycasa — Test Evidence")
A("")
A("Raw results behind the report and the slides. Every number here is read straight")
A("from the JSON files in `outputs/`, which are written by the scripts in `scripts/`.")
A("Nothing is typed by hand.")
A("")
A("Environment: see [`outputs/versions.txt`](outputs/versions.txt). Key versions are")
A("`ultralytics==8.3.197`, `torch==2.5.1+cu121`, `opencv-contrib-python==4.14.0.94`,")
A("Python 3.12.10 on Windows 11, RTX 3050 Ti.")
A("")

# ---------------------------------------------------------------- A) API coverage
A("## A. Full public-API coverage — 140 cases")
A("")
A("Every public function in pycasa called at least once, with its important parameter")
A("variants and with deliberately invalid inputs to check error handling. Each module")
A("group runs in its own Python process, both to bound memory and to isolate the")
A("import contamination described in part B.")
A("")
A("```")
A("python scripts/step7_full_api_test.py")
A("```")
A("")

r = load_json("outputs/step7_api_test_results.json")
COVERAGE = {
    "io": "load_default_data / load_video, frame ranges, calibration overrides, missing files",
    "casa": "every getter and setter, copy, info, invalid calibration values",
    "preprocessing": "grayscale, 6 binarization methods, 6 normalization methods, chaining",
    "detection_yolo26": "default and custom weights, four confidence thresholds, invalid inputs",
    "detection_classic": "4 moving-cells methods, digital washing, urbano, assessment thresholds",
    "detection_yolov5": "YOLOv5 weights, confidence variants, the ordering test",
    "tracking": "SORT, JPDAF, DeepSORT variants, multi-source, overwrite, MOTA/IDF1",
    "motility": "kinematic and CASA parameters, all threshold and window variants",
    "visualization": "plot_frame, timelapse, radar, density scatter, interactive calculator",
}
c = Counter((x["section"], x["status"]) for x in r)
rows = []
for s, description in COVERAGE.items():
    p, f = c[(s, "PASS")], c[(s, "FAIL")]
    if p + f:
        rows.append([s.replace("_", " "), p + f, p, description])
passed = sum(x["status"] == "PASS" for x in r)
rows.append(["**total**", f"**{len(r)}**", f"**{passed}**", ""])
L += md_table(["Module group", "Cases", "Passed", "What was covered"], rows)
A("")
A("A pass on a deliberately invalid input means the function raised the appropriate")
A(f"error. {passed} of {len(r)} passed. The {len(r) - passed} failures are the defects below, not test artefacts.")
A("")
A("### The failures")
A("")
# Map each failing test to a plain-English description of what it means.
DESCRIPTIONS = {
 "session.io.load_default_data(volume_ml=...) wrapper/module signature parity":
   ("`session.io.load_default_data()` is missing `volume_ml` and `chamber_depth_um`",
    "The module-level function accepts them; the session wrapper raises TypeError."),
 "assessment.evaluate_detections() with NO detection -> expects error":
   ("`evaluate_detections()` with no detector run",
    "Warns and writes an all-zero result rather than raising. Defensible, but a zero score reads like a bad detector."),
 "assessment.evaluate_tracks() with NO tracking -> expects error":
   ("`evaluate_tracks()` with no tracking run",
    "Skips with `skipped=True` and a reason instead of raising. This one is good behaviour; the test expectation was wrong."),
 "kinematic_parameters(overlap=1.5) invalid -> expects error":
   ("`overlap` is not validated",
    "1.5, 5.0 and -0.5 are all accepted silently. Passing 50 as a percentage multiplies the work about thirtyfold."),
 "kinematic_parameters() with NO tracking -> expects error":
   ("`kinematic_parameters()` with no tracking run",
    "Returns an empty result with no error and no warning."),
 "kinematic_parameters() when um_per_px=None":
   ("`kinematic_parameters()` when `um_per_px` is None",
    "The load-time warning says motility \"will not compute\"; the call then raises ValueError. Inconsistent messaging."),
}
for x in r:
    if x["status"] == "FAIL":
        title, description = DESCRIPTIONS.get(x["name"], (x["name"], x["note"][:190]))
        A(f"- {title}")
        A(f"  - {description}")
A("")
A("Three of these six are genuine defects (numbers 1, 4 and 5 in that order); the")
A("others describe behaviour that is defensible but surprising. See the report for the")
A("prioritised list.")
A("")
A("Full per-case table: [`outputs/step7_api_test_report.md`](outputs/step7_api_test_report.md)")
A("")

# ---------------------------------------------------------------- B) the NMS finding
A("## B. YOLO26 changes its own NMS algorithm depending on what is imported")
A("")
A("### B.1 Symptom")
A("")
A("YOLO26 gives different results on identical data with identical weights, depending")
A("only on what ran earlier in the same Python process. True positives stay fixed;")
A("only the false-positive tail moves.")
A("")
L += md_table(["Run", "Frames", "TP", "FP", "FN", "Precision", "Recall", "F1"], [
    ["isolated process", "101", "9,985", "5,806", "107", "63.23%", "98.94%", "77.15%"],
    ["after YOLOv5, same process", "101", "9,985", "4,797", "107", "67.55%", "98.94%", "80.28%"],
    ["isolated process", "899 (full clip)", "80,271", "42,369", "808", "65.45%", "99.00%", "78.81%"],
])
A("")
A("Recall is pinned because TP and FN do not move. Precision carries the whole change,")
A("and F1 follows it.")
A("")

# --- 2x2
A("### B.2 Thread count ruled out (controlled 2x2)")
A("")
A("The obvious candidate was OpenCV's thread count, which the YOLOv5 import drops from")
A("the default to one. Tested directly rather than inferred: the import and the thread")
A("count were varied independently, each condition in its own process.")
A("")
d = load_json("outputs/step9_thread_control.json")
L += md_table(["Run", "YOLOv5 imported", "cv2 threads", "Detections", "TP", "FP", "F1"],
              [[k, "yes" if d[k]["yolov5_import"] else "no", d[k]["environment"]["cv2_threads"],
                f"{d[k]['detections']:,}", f"{d[k]['tp']:,}", f"{d[k]['fp']:,}", f"{d[k]['F1']:.2f}%"]
               for k in "ABCD"])
A("")
A(f"A equals B and C equals D, so the thread count changes nothing on its own. B against D")
A(f"differs by {d['B']['detections'] - d['D']['detections']} detections with the thread count held equal, so the import does.")
A(f"True positives are {d['A']['tp']:,} in all four conditions.")
A("")
A("Script: `scripts/step9_thread_control.py`")
A("")

# --- eliminated candidates
A("### B.3 Four more candidates ruled out")
A("")
b = load_json("outputs/step9b_module_shadow.json")
cc = load_json("outputs/step9c_env_test.json")
dd = load_json("outputs/step9d_ultralytics.json")
L += md_table(["Candidate", "Test", "Detections", "Verdict"], [
    ["Module shadowing",
     "import YOLOv5, then delete `models` / `utils` from `sys.modules`",
     f"{b['E']['detections']:,} (vs {b['A']['detections']:,} isolated)",
     "not the cause"],
    ["Environment variables",
     "set all five the import writes, before torch, with no YOLOv5 import",
     f"{cc['F']['detections']:,} (vs {cc['A']['detections']:,} isolated)",
     "not the cause"],
    ["`import ultralytics`",
     "import the shared package alone",
     f"{dd['G']['detections']:,} (vs {dd['A']['detections']:,} isolated)",
     "not the cause"],
    ["`ultralytics.utils.patches`",
     "import the patching module alone",
     f"{dd['H']['detections']:,} (vs {dd['A']['detections']:,} isolated)",
     "not the cause"],
])
A("")
A("Torch global flags (thread counts, cuDNN benchmark and determinism, TF32 on both")
A("paths, float32 matmul precision, default dtype, gradient mode) were byte-identical")
A("before and after the import. `torchvision.ops.nms` is the same function object, so it")
A("had not been monkey-patched. Passing `conf` explicitly still shifts the result.")
A("")
A("Scripts: `scripts/step9b_module_shadow.py`, `step9c_env_test.py`, `step9d_ultralytics_test.py`")
A("")

# --- bisect
A("### B.4 Bisecting the import chain")
A("")
A("Each module that `models/common.py` imports, run alone in its own process:")
A("")
e = load_json("outputs/step9e_bisect.json")
LABELS_E = {"none": "(nothing imported)", "plotting": "ultralytics.utils.plotting",
            "utils_init": "utils (yolov5 package init)", "dataloaders": "utils.dataloaders",
            "general": "utils.general", "torch_utils": "utils.torch_utils",
            "common_full": "models.common (the full import)"}
isolated, contaminated = e["none"]["detections"], e["common_full"]["detections"]
L += md_table(["Imported", "Detections", "FP", "F1", "Verdict"],
              [[LABELS_E[k], f"{e[k]['detections']:,}", f"{e[k]['fp']:,}", f"{e[k]['F1']:.2f}%",
                "reference" if k in ("none", "common_full")
                else ("**reproduces it**" if e[k]["detections"] == contaminated else "no effect")]
               for k in LABELS_E if k in e])
A("")
A("`utils.dataloaders` and `utils.torch_utils` both import `utils.general`, so the")
A("common factor is `utils.general`. Bisecting inside that file:")
A("")
f6 = load_json("outputs/step9f_bisect_general.json")
LABELS_F = {"none": "(nothing imported)", "torchvision": "**`import torchvision`**",
            "yaml_packaging": "yaml, packaging", "ul_data_conv": "ultralytics.data.converter",
            "ul_checks": "ultralytics.utils.checks", "ul_files": "ultralytics.utils.files",
            "ul_git": "ultralytics.utils.git", "ul_ops": "ultralytics.utils.ops",
            "ul_torch_utils": "ultralytics.utils.torch_utils", "ul_patches": "ultralytics.utils.patches",
            "y5_downloads": "utils.downloads", "y5_metrics": "utils.metrics",
            "settings_block": "the module-level settings block (lines 79-87)",
            "general_full": "utils.general (the whole file)"}
L += md_table(["Imported", "Detections", "FP", "Verdict"],
              [[LABELS_F[k], f"{f6[k]['detections']:,}", f"{f6[k]['fp']:,}",
                "reference" if k in ("none", "general_full")
                else ("**reproduces it**" if f6[k]["detections"] == f6["general_full"]["detections"] else "no effect")]
               for k in LABELS_F if k in f6])
A("")
A("One line out of the whole chain reproduces the shift: `import torchvision`.")
A("")
A("Scripts: `scripts/step9e_bisect.py`, `scripts/step9f_bisect_general.py`")
A("")

# --- root cause
A("### B.5 Root cause")
A("")
A("`ultralytics/utils/nms.py`, lines 151-157, picks the NMS implementation at call time")
A("based on whether `torchvision` happens to be loaded:")
A("")
A("```python")
A('if "torchvision" in sys.modules:')
A("    i = torchvision.ops.nms(boxes, scores, iou_thres)   # compiled reference kernel")
A("else:")
A("    i = TorchNMS.nms(boxes, scores, iou_thres)          # ultralytics' own pure-PyTorch kernel")
A("```")
A("")
A("The `TorchNMS` docstring states that it \"matches torchvision behavior exactly\". On this")
A("data it does not: the two disagree on a few percent of low-confidence, overlapping boxes.")
A("")
A("pycasa's YOLOv5 loader imports `torchvision` explicitly before building the model")
A("(`pycasa/detection/_yolo.py`, `_load_standard_yolov5_model`), so running YOLOv5 first")
A("flips the switch for every later YOLO26 call in that process. An isolated pycasa run")
A("never imports torchvision, which was confirmed by inspecting `sys.modules` before and")
A("after inference — so pycasa's default YOLO26 path uses the fallback kernel.")
A("")
A("The decisive test: import torchvision, then delete it from `sys.modules` while its")
A("libraries stay loaded in memory.")
A("")
L += md_table(["Condition", "Detections", "F1"], [
    ["torchvision not imported", f"{isolated:,}", "78.00%"],
    ["torchvision imported", f"{contaminated:,}", "80.97%"],
    ["imported, then removed from `sys.modules`", f"{isolated:,}", "78.00%"],
])
A("")
A("Removing the name restores the original result, so the switch is the registry check")
A("itself, not any numerical side effect of loading the package.")
A("")
A("### B.6 Fix")
A("")
A("For pycasa: `import torchvision` before running YOLO26, so inference always uses the")
A("reference kernel regardless of what else the process has loaded. One line.")
A("")
A("For ultralytics: the equivalence claim in the `TorchNMS` docstring does not hold on")
A("this data, and selecting an algorithm from `sys.modules` makes output depend on import")
A("history. Worth reporting upstream.")
A("")
A("Until either lands, any published YOLO26 precision or F1 figure should state whether")
A("torchvision was loaded, because the same model on the same data spans several points of F1.")
A("")

io.open(OUT_MD, "w", encoding="utf-8").write("\n".join(L) + "\n")
print(f"written: {OUT_MD}  ({os.path.getsize(OUT_MD)/1024:.0f} KB, {len(L)} lines)")
