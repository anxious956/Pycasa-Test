"""Step 8: repeat steps 3, 5 and 6 over the FULL clip (899/901 frames, ~30 seconds).

Why: 101 frames is only a 3.4 second excerpt. Concentration and total count are
sensitive to the number of frames, since they are derived from the per-frame cell
average. We measure whether the full clip reduces that error appreciably.

Memory: 899 frames x 1280x1024x3 = ~3.5 GB. Each stage runs in its own process,
otherwise we hit MemoryError. YOLOv5 and YOLO26 must also run in separate
processes, otherwise importing YOLOv5 changes the YOLO26 result.

    python scripts/step8_full_clip.py            # all stages
    python scripts/step8_full_clip.py yolo26     # a single stage
"""
import os, sys, json, subprocess, gc

OUT = "outputs/step8_full_clip.json"
STAGES = ["yolov5", "yolo26", "moving_cells", "sort", "jpdaf", "gt_sort", "yolo26_sort"]


def _save(name, data):
    d = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    d[name] = data
    json.dump(d, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"  -> {name} saved")


def _clean(o):
    import numpy as np
    if isinstance(o, dict):  return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [_clean(v) for v in o]
    if isinstance(o, np.integer):  return int(o)
    if isinstance(o, np.floating): return float(o)
    if isinstance(o, np.ndarray):  return o.tolist()
    return o


def _load_largest_fit():
    """Load the longest clip that still fits in memory.

    The full clip needs 899 frames x 1280x1024x3 = 3.3 GB as a SINGLE contiguous
    block. The Windows commit limit means that block cannot always be allocated,
    so we step down until one fits. The frame count used is recorded in the result.
    """
    import pycasa as pc
    # NOTE: a failed attempt does not release its allocation immediately, so trying
    # 899 first and stepping down leaves no room for the later attempts. Hence we
    # start from a realistic value and call gc.collect() after every failure.
    target = os.environ.get("PYCASA_MAX_FRAMES")
    if target == "full":   sequence = [None, 800, 700, 600, 500]   # aiming for the full clip
    elif target:           sequence = [int(target)]
    else:                 sequence = [600, 500, 400, 300, 200]
    for ff in sequence:
        try:
            s = pc.io.load_default_data(final_frame=ff)
            print(f"  loaded frames: {s.get_video()['number_frame_used']}")
            return s
        except MemoryError:
            print(f"  {ff} frames did not fit, shrinking", flush=True)
            gc.collect()
    raise MemoryError("even the smallest attempt did not fit")


def run_stage(stage):
    s = _load_largest_fit()
    N = s.get_video()["number_frame_used"]

    if stage in ("yolov5", "yolo26", "moving_cells"):
        if stage == "moving_cells":
            s.detection.detect_moving_cells()
        else:
            s.detection.yolo(yolo_model=stage)
        s.assessment.evaluate_detections()
        a = s.get_assessment()
        _save(stage, {"frames_loaded": N, "detection": _clean(a["detection"]),
                      "frames": a["last_detection"]["frame_summary"]})

    elif stage in ("sort", "jpdaf"):
        getattr(s.tracking, stage)()                       # no detections -> GT only
        tr = s.get_tracks()[stage]["groundtruth"]
        n = len(tr)
        _save(stage, {"frames_loaded": N, "tracks": n,
                      "avg_track_length": round(sum(len(t) for t in tr.values()) / n, 2)})

    elif stage == "gt_sort":
        s.tracking.sort()
        s.motility.kinematic_parameters()
        s.motility.casa_parameters()
        m = s.get_motility()
        _save("gt_sort", {"frames_loaded": N, "casa": _clean(m["casa_parameters"]["groundtruth"]),
                          "kinematics": _summarise(m["kinematic_parameters"]["groundtruth"])})

    elif stage == "yolo26_sort":
        s.detection.yolo(yolo_model="yolo26")
        s.tracking.sort(skip_gt=True)
        s.motility.kinematic_parameters()
        s.motility.casa_parameters()
        m = s.get_motility()
        _save("yolo26_sort", {"frames_loaded": N, "casa": _clean(m["casa_parameters"]["yolo26"]),
                              "kinematics": _summarise(m["kinematic_parameters"]["yolo26"])})
    del s
    gc.collect()


def _summarise(kin):
    """Reduce the per-track window values to a single mean/std pair."""
    import numpy as np
    out = {}
    for p in ("VCL", "VSL", "VAP", "LIN", "ALH", "WOB", "STR", "MAD"):
        v = [x for t in kin.values() for x in t.get(p, [])]
        out[p] = [round(float(np.mean(v)), 2), round(float(np.std(v)), 2)] if v else None
    out["track_count"] = len(kin)
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_stage(sys.argv[1])
    else:
        if os.path.exists(OUT):
            os.remove(OUT)
        for a in STAGES:
            print(f"\n{'='*25} {a} {'='*25}", flush=True)
            p = subprocess.run([sys.executable, __file__, a],
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            for line in (p.stdout or "").splitlines():
                if any(k in line for k in ("loaded frames", "summary", "assessment results",
                                            "tracks=", "%rapid", "concentration", "-> ",
                                            "VCL=", "Error", "MemoryError")):
                    print("  " + line.strip())
            if p.returncode != 0:
                print(f"  !! {a} failed:", (p.stderr or "")[-300:])
        print("\nResults ->", os.path.abspath(OUT))
